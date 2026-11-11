import os
import json
import base64
import re
from io import BytesIO
from flask import Blueprint, request, jsonify, session, current_app
from datetime import date, datetime, timedelta
from models.database import get_db, login_required
from config import (
    get_ai_client, AI_MODEL, AI_VISION_MODEL,
    AI_MAX_TOKENS, AI_VISION_MAX_TOKENS, AI_TEMPERATURE,
)
from data.health_recipes import HEALTH_RECIPES

health_bp = Blueprint('health', __name__)

MAX_HISTORY = 50  # 每个用户最多保留最近 50 条对话


def _membership_is_vip(user_id):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT membership_expires_at FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            if not row or not row['membership_expires_at']:
                return False
            return row['membership_expires_at'] >= date.today()
    finally:
        conn.close()


def _chat_count_today(user_id):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) as cnt FROM conversation_history WHERE user_id = %s AND role='user' AND DATE(created_at) = %s",
                (user_id, date.today().isoformat())
            )
            return int(cur.fetchone()['cnt'] or 0)
    finally:
        conn.close()


def _tongue_counts(user_id):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM tongue_records WHERE user_id = %s", (user_id,))
            total = int(cur.fetchone()['cnt'] or 0)
            cur.execute("SELECT COUNT(*) as cnt FROM tongue_records WHERE user_id = %s AND DATE(created_at) = %s", (user_id, date.today().isoformat()))
            today = int(cur.fetchone()['cnt'] or 0)
            return total, today
    finally:
        conn.close()

SYSTEM_PROMPT = """
你是「慧食图谱」App 内的 AI 营养顾问。你回答必须专业、亲切、简洁。请使用 Markdown 组织回复，使内容层次清晰、美观易读。规则：
- 用 ## 标题分段
- 用 **加粗** 强调关键词
- 用 1. 2. 3. 数字编号展示步骤
- 用 - 列表项列举要点
- 避免代码块和表格，保持自然语言为主。

零、关于你身处的这个 App（重要，决定你如何组织答案）
- 你运行在「慧食图谱」里，它能给用户提供：首页的**今日三餐（早餐/午餐/晚餐）与热量、饮水打卡、运动计划**；「方案」页的 **AI 舌诊（舌象→体质→养生建议）** 和 **本对话**；「养生」页的 **20 道养生汤 / 20 道养生粥 / 20 道养生菜 / 20 款养生茶 / 养生产品**（每道都有真实的热量、蛋白质、碳水、食材、做法、功效）；「运动」页的六种运动与计时打卡；「我的」页的积分、订单、收藏、健康档案。
- 用户档案、今日已选餐食、舌诊结论、积分与打卡记录会以【用户全息档案】【今日实况】的形式提供给你。**优先引用这些真实数据**，不要凭空假设用户吃了什么。
- 当推荐具体菜品/汤粥茶时，**优先从上面这些真实菜谱里选**，并写出菜名 + 热量 + 推荐理由；用户可以在 App 里直接点开查看做法。
- 用户问"我今天该怎么吃""帮我分析舌诊""给我运动建议"时，要结合今日已选餐食与舌诊体质作答，并明确指出"你今天已经选了 X，热量 Y kcal，还差 Z"这类具体数字。

一、角色定位
- 你的身份是专业、严谨、富有同理心的营养顾问，目标是帮助用户通过科学饮食改善健康状况。
- 你绝不提供医疗诊断或替代医生处方。若用户提及疾病症状（如持续疼痛、高烧、急性不适等），必须首先建议其尽快就医，并说明你的建议不能替代专业诊疗。

二、知识范围与限制
1. 精通领域：
   - 食物营养成分、膳食指南（中国居民膳食指南、DASH饮食、地中海饮食等）
   - 特殊人群营养（孕婴、老人、运动员）
   - 慢病营养管理（糖尿病、高血压、痛风、肾病等）
   - 体重控制、食物过敏与不耐受
2. 绝对不做的：
   - 不提供具体的药物剂量、输液营养方案或侵入性治疗建议
   - 不推荐极端节食、排毒疗法、单一食物减肥法，或任何未经科学验证的"超级食物"
3. 知识库使用：
   - 你拥有以下完整食物和食谱数据库。当需要推荐具体菜品时，应基于用户的热量需求、健康状况（如控糖、降压、减脂）及口味偏好，从知识库中检索匹配项，并说明推荐理由（如低GI、高蛋白、富含膳食纤维等）。

三、回答输出规范
每次回答前，先评估信息完整性：
- 若用户缺少关键信息（年龄、性别、身高体重、活动强度、健康状况、饮食偏好），主动追问至少2-3项核心信息。
- 之后按照以下四个部分结构化输出（每部分用空行分隔）：

核心原则 → 具体食物选择 → 膳食搭配示例 → 注意事项

特别要求：
- 个性化量化：使用可操作的份量单位，如"一掌心大小的肉""半碗熟米饭""一个拳头大小的水果"，避免模糊表述如"适量""一些"。
- 避免绝对化：使用"通常建议""多数情况下""根据现有研究""可以优先考虑"等措辞，而不是"必须""绝对禁止""永远不要"。
- 安全底线：明确指出潜在风险（如"长期高钠饮食会增加高血压风险"），并鼓励用户咨询线下注册营养师进行一对一评估。

四、典型问答示例
用户：我查出糖尿病，应该怎么吃？
你：首先请咨询内分泌医生确认您的糖尿病分型及用药方案，本建议不能替代医疗治疗。在此基础上，为您提供饮食优化参考：
核心原则：控制餐后血糖平稳，优先选择低升糖指数（低GI）的碳水化合物，同时保证充足蛋白质和膳食纤维。
具体食物选择：
- 主食：用荞麦面、糙米、燕麦、杂豆替换白米饭、白面条。每餐主食约一拳头大小。
- 蔬菜：每天至少500g绿叶蔬菜（如菠菜、油菜、西兰花），先吃蔬菜再吃主食。
- 蛋白质：优选鱼、去皮禽肉、豆腐，每餐一掌心大小。
- 水果：血糖稳定时可选柚子、草莓、蓝莓，每次一小碗，两餐之间吃。
膳食搭配示例：
- 早餐：无糖酸奶100g + 燕麦南瓜羹一小碗 + 水煮蛋1个
- 午餐：杂粮饭半碗 + 清蒸鲈鱼100g + 蒜蓉西兰花150g
- 晚餐：番茄龙利鱼汤一碗 + 全麦馒头半个 + 凉拌黄瓜
注意事项：
- 进餐顺序：汤→蔬菜→蛋白质→主食。避免喝粥（尤其是煮得软烂的白粥）。
- 监测餐后2小时血糖，若波动大需调整碳水摄入量。
- 以上建议为通用版，强烈建议您到临床营养科制定个体化方案。

五、价值观与伦理
- 反对身材焦虑：不以单纯"减肥"为导向，强调长期健康、体能与代谢指标的改善。
- 尊重饮食文化差异：如素食、清真、地域特色（如川渝喜辣、广东喜清淡），不强行改变合理传统习惯。
- 主动揭露商业误导：例如"0蔗糖不等于低卡路里""无脂可能添加更多糖""酵素排毒缺乏科学依据"。
以上为AI营养助手完整规则。现在请以慧食图谱AI营养助手的身份，遵循所有规则，开始与用户进行专业交互。
        """


def _build_profile_text(user_id):
    conn = None
    try:
        conn = get_db()
        profile = {}
        diseases = []
        preferences = {}
        goals = []
        lifestyle = {}
        metadata = []
        tongue_row = None
        with conn.cursor() as cur:
            cur.execute("SELECT height, weight, age, gender, plan_tag FROM health_profile WHERE user_id=%s", (user_id,))
            row = cur.fetchone()
            if row:
                profile = {
                    "height": row["height"],
                    "weight": row["weight"],
                    "age": row["age"],
                    "gender": row["gender"],
                    "plan_tag": row["plan_tag"] or ""
                }
            cur.execute("SELECT disease, detail FROM medical_history WHERE user_id=%s", (user_id,))
            diseases = [{"disease": r["disease"], "detail": r["detail"]} for r in cur.fetchall()]
            cur.execute("SELECT taste_preference, food_restrictions, food_allergies, other_notes FROM user_preferences WHERE user_id=%s", (user_id,))
            row2 = cur.fetchone()
            if row2:
                preferences = row2
            cur.execute("SELECT goal FROM health_goals WHERE user_id=%s AND status='active'", (user_id,))
            goals = [r["goal"] for r in cur.fetchall()]
            cur.execute("SELECT sleep_schedule, exercise_frequency, alcohol_consumption, smoking, occupation, stress_level, daily_water_target, other_habits FROM lifestyle_info WHERE user_id=%s", (user_id,))
            row3 = cur.fetchone()
            if row3:
                lifestyle = row3
            cur.execute("SELECT meta_key, meta_value FROM user_metadata WHERE user_id=%s", (user_id,))
            metadata = [{"key": r["meta_key"], "value": r["meta_value"]} for r in cur.fetchall()]
            cur.execute("SELECT constitution_type, constitution_details FROM tongue_records WHERE user_id=%s ORDER BY created_at DESC LIMIT 1", (user_id,))
            tongue_row = cur.fetchone()
    except Exception:
        return "\n\u3010\u5f53\u524d\u7528\u6237\u5065\u5eb7\u6863\u6848\u3011\u65e0\u6cd5\u8bfb\u53d6\u5065\u5eb7\u6570\u636e\u3002\n"
    finally:
        if conn:
            conn.close()

    parts = []
    has_data = False

    if any([profile.get("height"), profile.get("weight"), profile.get("age")]):
        has_data = True
        sub = []
        if profile.get("height"): sub.append(f'\u8eab\u9ad8{profile["height"]}cm')
        if profile.get("weight"): sub.append(f'\u4f53\u91cd{profile["weight"]}kg')
        if profile.get("age"): sub.append(f'\u5e74\u9f84{profile["age"]}\u5c81')
        if profile.get("gender"): sub.append(f'\u6027\u522b{profile["gender"]}')
        if profile.get("plan_tag"): sub.append(f'\u5065\u5eb7\u6807\u7b7e\uff1a{profile["plan_tag"]}')
        parts.append("\u57fa\u672c\u4fe1\u606f\uff1a" + "\u3001".join(sub))

    if diseases:
        has_data = True
        d_parts = [f'{d["disease"]}({d["detail"]})' if d.get("detail") else d["disease"] for d in diseases]
        parts.append("\u65e2\u5f80\u75c5\u53f2\uff1a" + "\u3001".join(d_parts))

    pref_parts = []
    if preferences.get("taste_preference"):
        pref_parts.append(f'\u53e3\u5473\u504f\u597d: {preferences["taste_preference"]}')
    if preferences.get("food_restrictions"):
        pref_parts.append(f'\u996e\u98df\u9650\u5236: {preferences["food_restrictions"]}')
    if preferences.get("food_allergies"):
        pref_parts.append(f'\u98df\u7269\u8fc7\u654f: {preferences["food_allergies"]}')
    if preferences.get("other_notes"):
        pref_parts.append(f'\u5176\u4ed6\u8bf4\u660e: {preferences["other_notes"]}')
    if pref_parts:
        has_data = True
        parts.append("\u996e\u98df\u504f\u597d\uff1a" + "; ".join(pref_parts))

    if goals:
        has_data = True
        parts.append("\u5065\u5eb7\u76ee\u6807\uff1a" + "\u3001".join(goals))

    life_parts = []
    if lifestyle.get("sleep_schedule"):
        life_parts.append(f'\u4f5c\u606f: {lifestyle["sleep_schedule"]}')
    if lifestyle.get("exercise_frequency"):
        life_parts.append(f'\u8fd0\u52a8: {lifestyle["exercise_frequency"]}')
    if lifestyle.get("alcohol_consumption"):
        life_parts.append(f'\u996e\u9152: {lifestyle["alcohol_consumption"]}')
    if lifestyle.get("smoking"):
        life_parts.append(f'\u5438\u70df: {lifestyle["smoking"]}')
    if lifestyle.get("occupation"):
        life_parts.append(f'\u804c\u4e1a: {lifestyle["occupation"]}')
    if lifestyle.get("stress_level"):
        life_parts.append(f'\u538b\u529b: {lifestyle["stress_level"]}')
    if lifestyle.get("daily_water_target"):
        life_parts.append(f'\u6bcf\u65e5\u996e\u6c34\u76ee\u6807: {lifestyle["daily_water_target"]}ml')
    if lifestyle.get("other_habits"):
        life_parts.append(f'\u5176\u4ed6\u4e60\u60ef: {lifestyle["other_habits"]}')
    if life_parts:
        has_data = True
        parts.append("\u751f\u6d3b\u4e60\u60ef\uff1a" + "; ".join(life_parts))

    if tongue_row and tongue_row.get("constitution_type"):
        has_data = True
        tongue_text = f'\u4f53\u8d28: {tongue_row["constitution_type"]}'
        if tongue_row.get("constitution_details"):
            tongue_text += f' ({tongue_row["constitution_details"]})'
        parts.append("\u820c\u8bca\u4fe1\u606f\uff1a" + tongue_text)

    if metadata:
        has_data = True
        meta_parts = [f'{m["key"]}={m["value"]}' for m in metadata]
        parts.append("\u5176\u4ed6\u4fe1\u606f\uff1a" + "; ".join(meta_parts))

    if has_data:
        text = "\n".join(parts)
        return f"\n\u3010\u7528\u6237\u5168\u606f\u6863\u6848\u3011\n{text}\n\n\u8bf7\u5728\u540e\u7eed\u5bf9\u8bdd\u4e2d\u59cb\u7ec8\u57fa\u4e8e\u4ee5\u4e0a\u6863\u6848\u6570\u636e\u63d0\u4f9b\u4e2a\u6027\u5316\u5efa\u8bae\u3002\u5982\u679c\u53d1\u73b0\u7528\u6237\u63d0\u4f9b\u4e86\u65b0\u7684\u4e2a\u4eba\u4fe1\u606f\uff0c\u53ef\u4ee5\u5728\u56de\u590d\u4e2d\u4f7f\u7528 [SAVE_INFO: key=value] \u683c\u5f0f\u81ea\u52a8\u8bb0\u5f55\u3002\n"
    else:
        return "\n\u3010\u7528\u6237\u5168\u606f\u6863\u6848\u3011\u7528\u6237\u5c1a\u672a\u586b\u5199\u4e2a\u4eba\u4fe1\u606f\u3002\u8bf7\u5728\u9996\u6b21\u56de\u590d\u4e2d\u53cb\u5584\u5730\u5f15\u5bfc\u7528\u6237\u5230\u300c\u4e2a\u4eba\u4e2d\u5fc3\u300d\u586b\u5199\u5065\u5eb7\u6863\u6848\uff0c\u4ee5\u4fbf\u63d0\u4f9b\u7cbe\u51c6\u7684\u8425\u517b\u5efa\u8bae\u3002\n"

def _build_today_text(user_id):
    """「今日实况」：把 App 内真实产生的数据注入上下文，让 AI 能基于软件数据作答。"""
    today = date.today().isoformat()
    lines = []
    conn = None
    try:
        conn = get_db()
        with conn.cursor() as cur:
            # 今日三餐 + 今日养生
            cur.execute(
                "SELECT meal_type, food_name, calories, protein, carbs FROM daily_meals "
                "WHERE user_id=%s AND date=%s", (user_id, today)
            )
            rows = cur.fetchall()
            label = {
                'breakfast': '早餐', 'lunch': '午餐', 'dinner': '晚餐',
                'health_soup': '养生汤', 'health_porridge': '养生粥',
                'health_dish': '养生菜', 'health_tea': '养生茶',
            }
            meals, total = [], 0
            for r in rows:
                k = label.get(r['meal_type'], r['meal_type'])
                meals.append(f"{k}：{r['food_name']}（{int(r['calories'] or 0)}kcal）")
                total += int(r['calories'] or 0)
            if meals:
                lines.append("；".join(meals) + f"。今日已选合计 {total} kcal")
            else:
                lines.append("今日还没有在三餐里选任何菜品")

            # 今日运动
            cur.execute(
                "SELECT name, duration_seconds, calories FROM exercise_log "
                "WHERE user_id=%s AND date=%s", (user_id, today)
            )
            ex = cur.fetchall()
            if ex:
                exs = "、".join(f"{e['name']}{int((e['duration_seconds'] or 0)/60)}分钟（{int(e['calories'] or 0)}kcal）" for e in ex)
                lines.append("今日运动：" + exs)
            else:
                lines.append("今日还没有运动记录")

            # 今日打卡
            cur.execute(
                "SELECT type, detail, points_added FROM checkin_log WHERE user_id=%s AND date=%s",
                (user_id, today)
            )
            ck = cur.fetchall()
            if ck:
                lines.append("今日打卡：" + "、".join(f"{c['detail'] or c['type']}(+{c['points_added']})" for c in ck))

            # 积分与会员
            cur.execute("SELECT points, membership_expires_at, membership_plan FROM users WHERE id=%s", (user_id,))
            u = cur.fetchone()
            if u:
                vip = "会员" if (u['membership_expires_at'] and u['membership_expires_at'] >= date.today()) else "普通用户"
                lines.append(f"用户身份：{vip}，当前积分 {u['points']}")

            # 最近一次舌诊结论
            cur.execute(
                "SELECT constitution_type, analysis_result, created_at FROM tongue_records "
                "WHERE user_id=%s AND constitution_type IS NOT NULL AND constitution_type<>'' "
                "ORDER BY created_at DESC LIMIT 1", (user_id,)
            )
            t = cur.fetchone()
            if t:
                report = _parse_json_safe(t['analysis_result'])
                if report and report.get('constitution'):
                    lines.append(
                        "最近一次舌诊（%s）：体质 %s，健康分 %s；舌色%s、舌形%s、苔%s%s、%s；主要提示：%s"
                        % (
                            t['created_at'].strftime('%m-%d') if t['created_at'] else '-',
                            report.get('constitution'), report.get('health_score'),
                            report.get('tongue_color'), report.get('tongue_shape'),
                            report.get('coating_color'), report.get('coating_texture'),
                            report.get('moisture'),
                            "；".join(r.get('title', '') for r in (report.get('risks') or [])[:3])
                        )
                    )
                else:
                    lines.append("最近一次舌诊结论：" + str(t['constitution_type']))
    except Exception:
        return ""
    finally:
        if conn:
            conn.close()
    if not lines:
        return ""
    return "\n【今日实况】（以下为 App 内真实数据，回答时优先使用）\n" + "\n".join("- " + x for x in lines) + "\n"


def _parse_json_safe(text):
    """尽量从模型输出中解析出 JSON 对象。"""
    if not text:
        return None
    if isinstance(text, dict):
        return text
    s = str(text).strip()
    if s.startswith('```'):
        s = s.strip('`')
        if s.lower().startswith('json'):
            s = s[4:]
    start, end = s.find('{'), s.rfind('}')
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(s[start:end + 1])
    except Exception:
        return None


def _load_history(user_id, conversation_id=None):
    conn = None
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT role, content FROM conversation_history WHERE user_id=%s AND conversation_id=%s ORDER BY created_at ASC LIMIT %s",
                (user_id, conversation_id, MAX_HISTORY)
            )
            return [{"role": r["role"], "content": r["content"]} for r in cur.fetchall()]
    except Exception:
        return []
    finally:
        if conn:
            conn.close()


def _save_message(user_id, conversation_id, role, content):
    conn = None
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO conversation_history (user_id, conversation_id, role, content) VALUES (%s, %s, %s, %s)",
                (user_id, conversation_id, role, content)
            )
            conn.commit()
    except Exception:
        pass
    finally:
        if conn:
            conn.close()


def _trim_history(user_id, conversation_id=None):
    conn = None
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(
                """DELETE FROM conversation_history WHERE user_id=%s AND conversation_id=%s AND id NOT IN (
                    SELECT id FROM (
                        SELECT id FROM conversation_history WHERE user_id=%s AND conversation_id=%s
                        ORDER BY created_at DESC LIMIT %s
                    ) AS keep_ids
                )""",
                (user_id, conversation_id, user_id, conversation_id, MAX_HISTORY)
            )
            conn.commit()
    except Exception:
        pass
    finally:
        if conn:
            conn.close()


@health_bp.route('/ai_chat', methods=['POST'])
@login_required
def ai_chat():
    data = request.json
    user_message = data.get('message', '').strip()
    conversation_id = data.get('conversation_id')
    user_id = session['user_id']
    is_vip = _membership_is_vip(user_id)
    chat_limit = 20 if is_vip else 3
    if _chat_count_today(user_id) >= chat_limit:
        return jsonify({'error': '今日对话次数已用完，升级会员可享更多'}), 403

    # Auto-create conversation if not specified
    if not conversation_id:
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO conversations (user_id, title) VALUES (%s, %s)", (user_id, user_message[:20] or '新对话'))
                conn.commit()
                conversation_id = cur.lastrowid
        finally:
            conn.close()

    system_content = SYSTEM_PROMPT + _build_profile_text(user_id) + _build_today_text(user_id)
    db_history = _load_history(user_id, conversation_id)

    messages = [{"role": "system", "content": system_content}] + db_history
    messages.append({"role": "user", "content": user_message})

    try:
        response = get_ai_client().chat.completions.create(
            model=AI_MODEL,
            messages=messages,
            temperature=AI_TEMPERATURE,
            max_tokens=AI_MAX_TOKENS
        )
        ai_reply = response.choices[0].message.content
        if not ai_reply:
            ai_reply = "抱歉，我这次没能组织好回答，你可以再问一次吗？"
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        print("AI 调用错误 [" + error_type + "]:", error_msg)
        return jsonify({'error': error_msg, 'error_type': error_type}), 500

    try:
        _save_message(user_id, conversation_id, 'user', user_message)
        _save_message(user_id, conversation_id, 'assistant', ai_reply)
        _trim_history(user_id, conversation_id)
    except Exception:
        pass

    return jsonify({'reply': ai_reply, 'conversation_id': conversation_id})


@health_bp.route('/load_chat_history', methods=['GET'])
@login_required
def load_chat_history():
    user_id = session['user_id']
    conversation_id = request.args.get('conversation_id')
    conn = get_db()
    try:
        with conn.cursor() as cur:
            if conversation_id:
                cur.execute(
                    "SELECT role, content, created_at FROM conversation_history WHERE user_id=%s AND conversation_id=%s ORDER BY created_at ASC",
                    (user_id, conversation_id)
                )
            else:
                cur.execute(
                    "SELECT role, content, created_at FROM conversation_history WHERE user_id=%s ORDER BY created_at ASC",
                    (user_id,)
                )
            rows = cur.fetchall()
        history = []
        for r in rows:
            history.append({
                "role": r["role"],
                "content": r["content"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None
            })
        return jsonify({'history': history})
    finally:
        conn.close()


@health_bp.route('/clear_chat', methods=['POST'])
@login_required
def clear_chat():
    user_id = session['user_id']
    data = request.json or {}
    conversation_id = data.get('conversation_id')
    conn = get_db()
    try:
        with conn.cursor() as cur:
            if conversation_id:
                cur.execute("DELETE FROM conversation_history WHERE user_id=%s AND conversation_id=%s", (user_id, conversation_id))
            else:
                cur.execute("DELETE FROM conversation_history WHERE user_id=%s", (user_id,))
            conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()


@health_bp.route('/save_exercise', methods=['POST'])
@login_required
def save_exercise():
    data = request.json
    user_id = session['user_id']
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO exercise_log (user_id, type, name, duration_seconds, calories) VALUES (%s, %s, %s, %s, %s)",
                        (user_id, data['type'], data['name'], data['duration_seconds'], data['calories']))
            conn.commit()
        if data.get('award_points'):
            return checkin_internal('exercise', '运动打卡', 20)
        return jsonify({'success': True})
    finally:
        conn.close()


def checkin_internal(check_type, detail, points):
    user_id = session['user_id']
    today = date.today().isoformat()
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO checkin_log (user_id, date, type, detail, points_added) VALUES (%s, %s, %s, %s, %s)",
                        (user_id, today, check_type, detail, points))
            cur.execute("UPDATE users SET points = points + %s WHERE id = %s", (points, user_id))
            cur.execute("INSERT INTO points_log (user_id, change_amount, reason) VALUES (%s, %s, %s)",
                        (user_id, points, f"打卡-{check_type}"))
            conn.commit()
        return jsonify({'success': True, 'points_added': points})
    finally:
        conn.close()


@health_bp.route('/get_exercise_records', methods=['GET'])
@login_required
def get_exercise_records():
    user_id = session['user_id']
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT type, name, duration_seconds, calories, date FROM exercise_log WHERE user_id = %s ORDER BY date DESC", (user_id,))
            records = cur.fetchall()
        return jsonify({'records': records})
    finally:
        conn.close()


@health_bp.route('/health_recipes', methods=['GET'])
@login_required
def get_health_recipes():
    return jsonify(HEALTH_RECIPES)

# ========== Conversation management ==========
@health_bp.route('/conversations', methods=['GET'])
@login_required
def list_conversations():
    user_id = session['user_id']
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, title, created_at FROM conversations WHERE user_id=%s ORDER BY created_at DESC",
                (user_id,)
            )
            rows = cur.fetchall()
        result = []
        for r in rows:
            result.append({
                "id": r["id"],
                "title": r["title"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None
            })
        return jsonify({'conversations': result})
    finally:
        conn.close()

@health_bp.route('/conversations/new', methods=['POST'])
@login_required
def new_conversation():
    user_id = session['user_id']
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO conversations (user_id, title) VALUES (%s, '新对话')", (user_id,))
            conn.commit()
            conv_id = cur.lastrowid
        return jsonify({'conversation_id': conv_id, 'title': '新对话'})
    finally:
        conn.close()

@health_bp.route('/conversations/<int:conv_id>', methods=['DELETE'])
@login_required
def delete_conversation(conv_id):
    user_id = session['user_id']
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM conversations WHERE id=%s AND user_id=%s", (conv_id, user_id))
            conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()

# ========== Tongue Diagnosis Endpoints ==========

@health_bp.route('/tongue/upload', methods=['POST'])
@login_required
def tongue_upload():
    user_id = session['user_id']
    file = request.files.get('image')
    if not file:
        return jsonify({'error': 'no image file'}), 400

    # 先做配额校验，避免超限时留下垃圾文件
    total_tongue, today_tongue = _tongue_counts(user_id)
    if _membership_is_vip(user_id):
        if today_tongue >= 2:
            return jsonify({'error': '会员每日舌诊次数已用完，明天再来吧'}), 403
    else:
        if total_tongue >= 5:
            return jsonify({'error': '普通用户舌诊次数已用完，升级会员可享每日2次'}), 403

    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'tongue')
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"tongue_{user_id}_{int(datetime.now().timestamp())}.jpg"
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    source = request.form.get('source', 'upload')
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO tongue_records (user_id, image_path, source) VALUES (%s, %s, %s)",
                (user_id, f'uploads/tongue/{filename}', source)
            )
            conn.commit()
            record_id = cur.lastrowid
        return jsonify({
            'success': True,
            'record_id': record_id,
            'image_url': f'/static/uploads/tongue/{filename}'
        })
    finally:
        conn.close()


@health_bp.route('/tongue/records', methods=['GET'])
@login_required
def tongue_records():
    user_id = session['user_id']
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, image_path, source, analysis_result, constitution_type, constitution_details, created_at FROM tongue_records WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,)
            )
            rows = cur.fetchall()
        records = []
        for r in rows:
            records.append({
                'id': r['id'],
                'image_url': '/static/' + r['image_path'] if r['image_path'] else None,
                'source': r['source'],
                'analysis_result': r['analysis_result'],
                'constitution_type': r['constitution_type'],
                'constitution_details': r['constitution_details'],
                'created_at': r['created_at'].isoformat() if r['created_at'] else None
            })
        return jsonify({'records': records})
    finally:
        conn.close()


# ========== AI Metadata Extraction ==========

@health_bp.route('/ai_extract_metadata', methods=['POST'])
@login_required
def ai_extract_metadata():
    data = request.json
    ai_content = data.get('content', '')
    user_id = session['user_id']
    import re
    matches = re.findall(r'\[SAVE_INFO:\s*(.+?)\s*=\s*(.+?)\]', ai_content)
    saved = []
    if matches:
        conn = get_db()
        try:
            with conn.cursor() as cur:
                for key, value in matches:
                    key = key.strip()
                    value = value.strip()
                    if key and value:
                        sql = (
                            "INSERT INTO user_metadata (user_id, meta_key, meta_value, source) "
                            "VALUES (%s, %s, %s, 'ai') "
                            "ON DUPLICATE KEY UPDATE meta_value = VALUES(meta_value), source = 'ai'"
                        )
                        cur.execute(sql, (user_id, key, value))
                        saved.append({'key': key, 'value': value})
                conn.commit()
        finally:
            conn.close()
    return jsonify({'saved': saved, 'count': len(saved)})

# ========== Tongue Diagnosis (DeepSeek Vision) ==========

TONGUE_VISION_PROMPT = """你是一位资深的中医舌诊专家，同时精通现代营养学。请仔细观察这张舌象照片，完成规范的中医舌诊，并严格以 JSON 输出结果。

【观察维度】请逐项判断：
1. 舌色（淡白/淡红/红/绛红/青紫/紫暗，可带"边尖红"等描述）
2. 舌形（正常/胖大/瘦薄/齿痕/裂纹/点刺/瘀斑，可多选）
3. 苔色（薄白/白/黄/灰/黑/无苔）
4. 苔质（薄/厚/腻/腐/剥落/少苔）
5. 润燥（润/偏润/少津/干燥/滑腻）
6. 舌下络脉（若不可见填"不可见"）

【体质判定】依据中医九种体质（平和质、气虚质、阳虚质、阴虚质、痰湿质、湿热质、血瘀质、气郁质、特禀质）给出主判定与可能的兼夹体质。

【重要约束】
- 只描述你真正从图上看到的特征，看不清就写"不清晰"，不要编造。
- 健康分为 0-100 的整数，反映当前舌象偏离平和质的程度。
- diet_advice 里要给出**具体到食材/菜品**的建议，而不是"多吃蔬菜"这种空话。
- recipe_keywords 给 5 个适合该体质的食材或菜名关键词，用于在 App 的养生汤/粥/菜/茶库中检索。
- 不要给出任何疾病诊断，disclaimer 里要说明这不能替代医疗。

【输出 JSON 结构】（必须严格按此结构，不要输出任何 JSON 之外的内容）
{
  "tongue_color": "舌色",
  "tongue_shape": "舌形",
  "coating_color": "苔色",
  "coating_texture": "苔质",
  "moisture": "润燥",
  "sublingual_vein": "舌下络脉",
  "constitution": "主体质，如：痰湿质",
  "constitution_secondary": ["兼夹体质1", "兼夹体质2"],
  "health_score": 72,
  "summary": "两三句话的整体结论",
  "indicators": [
    {"label": "舌色", "value": "淡红", "status": "normal|attention|warning", "comment": "一句话解读"}
  ],
  "risks": [
    {"title": "风险点标题", "level": "高|中|低", "detail": "为什么会出现、可能带来什么"}
  ],
  "diet_advice": [
    {"action": "宜|忌", "item": "具体食物或菜品名", "reason": "为什么"}
  ],
  "lifestyle_advice": [
    {"title": "建议标题", "detail": "具体怎么做"}
  ],
  "recipe_keywords": ["关键词1", "关键词2", "关键词3", "关键词4", "关键词5"],
  "disclaimer": "本结果由 AI 基于舌象照片生成，仅供参考，不能替代专业医疗诊断。"
}"""


def _build_tongue_user_text(user_id):
    """给视觉模型补充用户的体质背景，让结论与档案呼应。"""
    parts = []
    conn = None
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT height, weight, age, gender FROM health_profile WHERE user_id=%s", (user_id,)
            )
            p = cur.fetchone()
            if p and (p['age'] or p['gender']):
                parts.append(f"身高 {p['height'] or '-'}cm，体重 {p['weight'] or '-'}kg，{p['age'] or '-'}岁，{p['gender'] or ''}")
            cur.execute("SELECT disease, detail FROM medical_history WHERE user_id=%s", (user_id,))
            mh = cur.fetchall()
            if mh:
                parts.append("既往/家族病史：" + "、".join(
                    f"{m['disease']}{('（' + m['detail'] + '）') if m['detail'] else ''}" for m in mh))
            cur.execute(
                "SELECT taste_preference, food_restrictions, food_allergies FROM user_preferences WHERE user_id=%s",
                (user_id,)
            )
            pref = cur.fetchone()
            if pref:
                bits = []
                if pref['taste_preference']: bits.append(f"口味偏好 {pref['taste_preference']}")
                if pref['food_restrictions']: bits.append(f"饮食限制 {pref['food_restrictions']}")
                if pref['food_allergies']: bits.append(f"过敏 {pref['food_allergies']}")
                if bits:
                    parts.append("；".join(bits))
            cur.execute(
                "SELECT sleep_schedule, exercise_frequency, stress_level, occupation FROM lifestyle_info WHERE user_id=%s",
                (user_id,)
            )
            ls = cur.fetchone()
            if ls:
                bits = []
                if ls['occupation']: bits.append(f"职业 {ls['occupation']}")
                if ls['sleep_schedule']: bits.append(f"作息 {ls['sleep_schedule']}")
                if ls['exercise_frequency']: bits.append(f"运动 {ls['exercise_frequency']}")
                if ls['stress_level']: bits.append(f"压力 {ls['stress_level']}")
                if bits:
                    parts.append("；".join(bits))
    except Exception:
        pass
    finally:
        if conn:
            conn.close()
    if not parts:
        return "请直接依据照片进行舌诊。"
    return (
        "【用户背景，供参考，但不要被它带偏观察】\n"
        + "\n".join("- " + x for x in parts)
        + "\n请结合上述背景，在 diet_advice 中给出贴合该用户的建议，但仍以照片所见为准。"
    )


def _match_recipes(keywords, limit=6):
    """按关键词从真实养生菜谱库里检索推荐条目。"""
    if not keywords:
        return []
    hits = []
    seen = set()
    groups = [
        ('soup', '养生汤', '汤品类'), ('porridge', '养生粥', '粥类'),
        ('dish', '养生菜', '菜品类'), ('tea', '养生茶', '茶饮'),
    ]
    for key, label, folder in groups:
        for item in HEALTH_RECIPES.get(key, []):
            name = item.get('name', '')
            if name in seen:
                continue
            haystack = name + str(item.get('effect', '')) + str(item.get('ingredients', '')) + str(item.get('intro', ''))
            if any(k and k in haystack for k in keywords):
                seen.add(name)
                hits.append({
                    'name': name,
                    'kind': key,
                    'kind_label': label,
                    'calories': item.get('calories'),
                    'protein': item.get('protein'),
                    'carbs': item.get('carbs'),
                    'price': item.get('price'),
                    'effect': item.get('effect', ''),
                    'img': f"/static/images/{folder}/{name}.png",
                })
            if len(hits) >= limit:
                return hits
    return hits


def _normalize_report(report, keywords):
    """补齐缺省字段，保证前端永远拿到完整结构。"""
    if not isinstance(report, dict):
        report = {}
    out = {
        'tongue_color': report.get('tongue_color') or '不清晰',
        'tongue_shape': report.get('tongue_shape') or '不清晰',
        'coating_color': report.get('coating_color') or '不清晰',
        'coating_texture': report.get('coating_texture') or '不清晰',
        'moisture': report.get('moisture') or '不清晰',
        'sublingual_vein': report.get('sublingual_vein') or '不可见',
        'constitution': report.get('constitution') or '平和质',
        'constitution_secondary': [x for x in (report.get('constitution_secondary') or []) if x][:3],
        'health_score': report.get('health_score'),
        'summary': report.get('summary') or '',
        'indicators': [],
        'risks': [],
        'diet_advice': [],
        'lifestyle_advice': [],
        'recipe_keywords': report.get('recipe_keywords') or keywords or [],
        'disclaimer': report.get('disclaimer') or '本结果由 AI 基于舌象照片生成，仅供参考，不能替代专业医疗诊断。',
    }
    try:
        out['health_score'] = max(0, min(100, int(out['health_score'])))
    except Exception:
        out['health_score'] = None

    for it in (report.get('indicators') or [])[:8]:
        if not isinstance(it, dict):
            continue
        st = str(it.get('status') or 'normal').lower()
        if st not in ('normal', 'attention', 'warning'):
            st = 'normal'
        out['indicators'].append({
            'label': it.get('label') or '',
            'value': it.get('value') or '',
            'status': st,
            'comment': it.get('comment') or '',
        })
    for it in (report.get('risks') or [])[:5]:
        if not isinstance(it, dict):
            continue
        lv = str(it.get('level') or '中')
        if lv not in ('高', '中', '低'):
            lv = '中'
        out['risks'].append({
            'title': it.get('title') or '',
            'level': lv,
            'detail': it.get('detail') or '',
        })
    for it in (report.get('diet_advice') or [])[:8]:
        if not isinstance(it, dict):
            continue
        act = it.get('action') or '宜'
        out['diet_advice'].append({
            'action': act if act in ('宜', '忌') else '宜',
            'item': it.get('item') or '',
            'reason': it.get('reason') or '',
        })
    for it in (report.get('lifestyle_advice') or [])[:6]:
        if not isinstance(it, dict):
            continue
        out['lifestyle_advice'].append({
            'title': it.get('title') or '',
            'detail': it.get('detail') or '',
        })
    return out


@health_bp.route('/tongue/diagnose', methods=['POST'])
@login_required
def tongue_diagnose():
    """用 DeepSeek 视觉模型做舌诊，输出结构化报告（不依赖任何第三方图床）。"""
    data = request.json or {}
    record_id = data.get('record_id')
    if not record_id:
        return jsonify({'error': 'record_id required'}), 400

    user_id = session['user_id']
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT image_path FROM tongue_records WHERE id=%s AND user_id=%s", (record_id, user_id))
            row = cur.fetchone()
            if not row:
                return jsonify({'error': 'record not found'}), 404

            image_path = os.path.join(current_app.root_path, 'static', row['image_path'])
            if not os.path.exists(image_path):
                return jsonify({'error': 'image file not found'}), 404

            # ---- Step 1: 压缩图片为 base64 data URL，直接喂给视觉模型 ----
            try:
                from PIL import Image
                with Image.open(image_path) as im:
                    im = im.convert('RGB')
                    w, h = im.size
                    if max(w, h) > 1280:
                        scale = 1280.0 / max(w, h)
                        im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
                    buf = BytesIO()
                    im.save(buf, format='JPEG', quality=88)
                    raw = buf.getvalue()
            except Exception:
                with open(image_path, 'rb') as f:
                    raw = f.read()
            b64 = base64.b64encode(raw).decode()
            data_url = 'data:image/jpeg;base64,' + b64

            # ---- Step 2: 调用视觉模型 ----
            try:
                response = get_ai_client().chat.completions.create(
                    model=AI_VISION_MODEL,
                    messages=[
                        {"role": "system", "content": TONGUE_VISION_PROMPT},
                        {"role": "user", "content": [
                            {"type": "text", "text": _build_tongue_user_text(user_id)},
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ]},
                    ],
                    temperature=0.3,
                    max_tokens=AI_VISION_MAX_TOKENS,
                )
                content = response.choices[0].message.content
            except Exception as e:
                print("舌诊视觉模型错误 [" + type(e).__name__ + "]:", str(e))
                return jsonify({'success': False, 'error': 'AI 舌诊服务暂时不可用，请稍后重试'}), 502

            report = _parse_json_safe(content)
            if not report:
                print("舌诊 JSON 解析失败，原始输出：", (content or '')[:500])
                return jsonify({'success': False, 'error': '舌诊分析结果解析失败，请重试'}), 502

            report = _normalize_report(report, [])
            recipes = _match_recipes(report.get('recipe_keywords'), limit=6)
            report['recommended_recipes'] = recipes

            constitution_type = report['constitution']
            details = {
                'summary': report['summary'],
                'indicators': report['indicators'],
                'risks': report['risks'],
                'diet_advice': report['diet_advice'],
                'lifestyle_advice': report['lifestyle_advice'],
                'recommended_recipes': recipes,
            }
            analysis_result = json.dumps(report, ensure_ascii=False)
            constitution_details = json.dumps(details, ensure_ascii=False)

            cur.execute("""
                UPDATE tongue_records
                SET analysis_result=%s, constitution_type=%s, constitution_details=%s
                WHERE id=%s
            """, (analysis_result, constitution_type, constitution_details, record_id))
            conn.commit()

            return jsonify({
                'success': True,
                'record_id': record_id,
                'constitution_type': constitution_type,
                'report': report,
                'image_url': '/static/' + row['image_path'],
            })
    finally:
        conn.close()


@health_bp.route('/tongue/report/<int:record_id>', methods=['GET'])
@login_required
def tongue_report_detail(record_id):
    """读取一条舌诊的完整结构化报告（历史记录回看用）。"""
    user_id = session['user_id']
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, image_path, source, analysis_result, constitution_type, created_at "
                "FROM tongue_records WHERE id=%s AND user_id=%s", (record_id, user_id)
            )
            row = cur.fetchone()
        if not row:
            return jsonify({'error': '记录不存在'}), 404
        report = _parse_json_safe(row['analysis_result'])
        if not report:
            report = {
                'constitution': row['constitution_type'] or '未分析',
                'summary': (row['analysis_result'] or '这条记录是旧版舌诊数据，重新拍照可生成完整报告。'),
                'indicators': [], 'risks': [], 'diet_advice': [],
                'lifestyle_advice': [], 'recommended_recipes': [],
                'health_score': None, 'legacy': True,
            }
        else:
            report = _normalize_report(report, [])
            if not report.get('recommended_recipes'):
                report['recommended_recipes'] = _match_recipes(report.get('recipe_keywords'), limit=6)
        return jsonify({
            'success': True,
            'id': row['id'],
            'image_url': '/static/' + row['image_path'] if row['image_path'] else None,
            'created_at': row['created_at'].isoformat() if row['created_at'] else None,
            'report': report,
        })
    finally:
        conn.close()


NUTRITION_INSIGHT_PROMPT = """你是「慧食图谱」的营养分析师。用户刚打开今日营养详情页，你要用一句话点出今天最关键的缺口，并给出可执行的补足方案。

只输出 JSON，不要任何解释文字、不要代码块。结构：
{
  "headline": "一句 26 字以内的结论，必须先给判断再给原因，例如：蛋白质只到 62%，晚餐该补一份手掌大的清蒸鱼",
  "detail": "两句话解释今天的数据特点（60 字以内）",
  "tone": "good | warn | bad",
  "focus": "protein | carb | calorie | water | exercise | balanced",
  "suggestions": [
    {"title": "行动标题（8 字以内）", "text": "具体做什么（30 字以内）", "kind": "dish | soup | porridge | tea | water | exercise"}
  ]
}

要求：
- suggestions 给 2 到 3 条，必须具体到食材与份量，不要「注意饮食」这类空话。
- 如果今天三餐完全没选（热量为 0），tone 用 "warn"，headline 要直接指出「今天还没选菜」，suggestions 引导去选三餐。
- 如果各项都已达标，tone 用 "good"，建议转向「维持」与「微调」。
- 严禁编造用户没有的数据；只依据给出的数字判断。"""


_nutrition_insight_cache = {}


@health_bp.route('/nutrition_insight', methods=['GET'])
@login_required
def nutrition_insight():
    """今日营养 AI 结论：把冷冰冰的数字翻译成一句人话 + 补足方案。"""
    user_id = session['user_id']
    today = date.today().isoformat()
    cache_key = (user_id, today)

    force = request.args.get('refresh') == '1'
    cached = _nutrition_insight_cache.get(cache_key)
    if cached and not force:
        return jsonify({'success': True, 'cached': True, **cached})

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT meal_type, food_name, calories, protein, carbs FROM daily_meals "
                "WHERE user_id=%s AND date=%s", (user_id, today)
            )
            rows = cur.fetchall()
            cur.execute("SELECT COUNT(*) as cnt FROM checkin_log WHERE user_id=%s AND date=%s AND type='water'",
                        (user_id, today))
            water_cups = int(cur.fetchone()['cnt'] or 0)
            cur.execute(
                "SELECT COALESCE(SUM(calories),0) as cals, COALESCE(SUM(duration_seconds),0) as secs "
                "FROM exercise_log WHERE user_id=%s AND DATE(date)=%s", (user_id, today))
            ex = cur.fetchone()
            cur.execute("SELECT height, weight, age, gender FROM health_profile WHERE user_id=%s", (user_id,))
            profile = cur.fetchone()
            cur.execute("SELECT constitution_type, constitution_details FROM tongue_records "
                        "WHERE user_id=%s AND constitution_type IS NOT NULL AND constitution_type<>'' "
                        "ORDER BY created_at DESC, id DESC LIMIT 1", (user_id,))
            tongue = cur.fetchone()
    finally:
        conn.close()

    label = {'breakfast': '早餐', 'lunch': '午餐', 'dinner': '晚餐',
             'health_soup': '养生汤', 'health_porridge': '养生粥',
             'health_dish': '养生菜', 'health_tea': '养生茶'}
    total_cal = sum(float(r['calories'] or 0) for r in rows)
    total_pro = sum(float(r['protein'] or 0) for r in rows)
    total_carb = sum(float(r['carbs'] or 0) for r in rows)
    meal_lines = [f"{label.get(r['meal_type'], r['meal_type'])}：{r['food_name']}（{round(float(r['calories'] or 0))} kcal）" for r in rows]

    # 目标热量（Mifflin-St Jeor × 活动系数）
    target_cal = 2000
    if profile:
        try:
            h = float(profile.get('height') or 0)
            w = float(profile.get('weight') or 0)
            a = int(profile.get('age') or 0)
            if h and w and a:
                is_male = (profile.get('gender') or '') in ('男', 'male', 'Male')
                bmr = 10 * w + 6.25 * h - 5 * a + (5 if is_male else -161)
                target_cal = round(max(1200, min(3500, bmr * 1.375)))
        except (TypeError, ValueError):
            target_cal = 2000
    target_pro = round(target_cal * 0.20 / 4)
    target_carb = round(target_cal * 0.55 / 4)
    exercise_min = round(float(ex['secs'] or 0) / 60)
    exercise_cal = round(float(ex['cals'] or 0))

    profile_bits = []
    if profile:
        if profile.get('height') and profile.get('weight'):
            profile_bits.append(f"身高 {profile['height']}cm 体重 {profile['weight']}kg")
        if profile.get('age'):
            profile_bits.append(f"{profile['age']} 岁")
        if profile.get('gender'):
            profile_bits.append(str(profile['gender']))
    if tongue and tongue.get('constitution_type'):
        profile_bits.append(f"最近舌诊体质：{tongue['constitution_type']}")

    user_text = (
        f"【今日数据】\n"
        f"已选餐次：\n" + ("\n".join(meal_lines) if meal_lines else "（今天一餐都没选）") + "\n"
        f"热量 {round(total_cal)} / 目标 {target_cal} kcal\n"
        f"蛋白质 {round(total_pro, 1)} / 目标 {target_pro} g\n"
        f"碳水 {round(total_carb, 1)} / 目标 {target_carb} g\n"
        f"饮水 {water_cups * 200} / 1600 ml（{water_cups} 杯）\n"
        f"运动 {exercise_min} 分钟，消耗 {exercise_cal} kcal\n"
        f"【用户】{'；'.join(profile_bits) if profile_bits else '档案未填写'}\n"
    )

    try:
        client = get_ai_client()
        resp = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {'role': 'system', 'content': NUTRITION_INSIGHT_PROMPT},
                {'role': 'user', 'content': user_text},
            ],
            temperature=0.4,
            max_tokens=AI_MAX_TOKENS,
            response_format={'type': 'json_object'},
        )
        raw = resp.choices[0].message.content or ''
        parsed = _parse_json_safe(raw) or {}
    except Exception as e:
        print(f"营养结论 AI 调用错误 [{type(e).__name__}]: {e}")
        parsed = {}

    headline = (parsed.get('headline') or '').strip()
    if not headline:
        if total_cal <= 0:
            headline = '今天还没选菜，先把三餐定下来吧'
            tone, focus = 'warn', 'calorie'
        elif total_pro < target_pro * 0.6:
            headline = f'蛋白质只到 {round(total_pro / target_pro * 100) if target_pro else 0}%，晚餐该补一份优质蛋白'
            tone, focus = 'warn', 'protein'
        elif total_cal < target_cal * 0.6:
            headline = '今天热量偏低，容易晚上饿，建议加一份主食'
            tone, focus = 'warn', 'calorie'
        else:
            headline = '今天的整体搭配还不错，保持住'
            tone, focus = 'good', 'balanced'
    else:
        tone = parsed.get('tone') if parsed.get('tone') in ('good', 'warn', 'bad') else 'warn'
        focus = parsed.get('focus') or 'balanced'

    suggestions = parsed.get('suggestions')
    if not isinstance(suggestions, list) or not suggestions:
        suggestions = [
            {'title': '补蛋白', 'text': f'晚餐加一份清蒸鱼或鸡胸，约补 {max(0, target_pro - round(total_pro))} g 蛋白',
             'kind': 'dish'},
            {'title': '先喝水', 'text': f'今天还差 {max(0, 8 - water_cups)} 杯水，每小时一杯', 'kind': 'water'},
        ]
    clean_sugs = []
    for s in suggestions[:3]:
        if not isinstance(s, dict):
            continue
        clean_sugs.append({
            'title': str(s.get('title') or '建议')[:16],
            'text': str(s.get('text') or '')[:60],
            'kind': s.get('kind') if s.get('kind') in ('dish', 'soup', 'porridge', 'tea', 'water', 'exercise') else 'dish',
        })

    payload = {
        'headline': headline[:60],
        'detail': str(parsed.get('detail') or '')[:120],
        'tone': tone,
        'focus': focus,
        'suggestions': clean_sugs,
        'metrics': {
            'calories': round(total_cal), 'target_calories': target_cal,
            'protein': round(total_pro, 1), 'target_protein': target_pro,
            'carbs': round(total_carb, 1), 'target_carbs': target_carb,
            'water_cups': water_cups, 'water_target': 8,
            'exercise_minutes': exercise_min, 'exercise_calories': exercise_cal,
        },
    }
    _nutrition_insight_cache[cache_key] = payload
    return jsonify({'success': True, 'cached': False, **payload})
