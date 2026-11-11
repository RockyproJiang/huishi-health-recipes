import os
from flask import Blueprint, request, jsonify, session, current_app
from datetime import date, datetime
from models.database import get_db, login_required
from config import (
    get_ai_client,
    TONGUE_APPCODE,
    TONGUE_DIAGNOSE_URL,
    IMG_HOST_IMGBB_KEY,
    IMG_HOST_FREEIMAGE_KEY,
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
你是慧食图谱的AI营养助手。你的回答必须专业、亲切、简洁。请使用Markdown格式来组织你的回复，使内容层次清晰、美观易读。规则：
- 用 ## 标题分段
- 用 **加粗** 强调关键词
- 用 1. 2. 3. 数字编号展示步骤
- 用 - 列表项列举要点
- 避免代码块和表格，保持自然语言为主。

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

    system_content = SYSTEM_PROMPT + _build_profile_text(user_id)
    db_history = _load_history(user_id, conversation_id)

    messages = [{"role": "system", "content": system_content}] + db_history
    messages.append({"role": "user", "content": user_message})

    try:
        response = get_ai_client().chat.completions.create(
            model="astron-code-latest",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        ai_reply = response.choices[0].message.content
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
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'tongue')
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"tongue_{user_id}_{int(datetime.now().timestamp())}.jpg"
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    total_tongue, today_tongue = _tongue_counts(user_id)
    if _membership_is_vip(user_id):
        if today_tongue >= 2:
            return jsonify({'error': '会员每日舌诊次数已用完'}), 403
    else:
        if total_tongue >= 5:
            return jsonify({'error': '普通用户舌诊次数已用完，升级会员可享每日2次'}), 403
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

# ========== Tongue Diagnosis API ==========
import base64
import json
import requests

@health_bp.route('/tongue/diagnose', methods=['POST'])
@login_required
def tongue_diagnose():
    """Call tongue diagnosis API with uploaded image using V2 face-tongue detect."""
    data = request.json
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

            # ---- Step 1: Upload to public image host ----
            public_url = _upload_to_public_host(image_path)
            if not public_url:
                return jsonify({'success': False, 'msg': '无法上传图片到公开图床，请稍后重试'})

            appcode = TONGUE_APPCODE
            json_headers = {
                'Authorization': 'APPCODE ' + appcode,
                'Content-Type': 'application/json; charset=UTF-8'
            }

            # ---- Step 2: 舌诊图像分析接口（网关地址由环境变量配置）----
            v2_url = TONGUE_DIAGNOSE_URL
            v2_body = {'scene': 1, 'tf_image': public_url}
            v2_resp = requests.post(v2_url, json=v2_body, headers=json_headers, timeout=60)
            v2_resp.raise_for_status()
            v2 = v2_resp.json()

            if not v2.get('success'):
                return jsonify({'success': False, 'msg': '舌诊API调用失败: ' + str(v2.get('msg', v2.get('code', 'unknown')))})

            v2_data = v2.get('data', {})

            # ---- Step 3: Process results ----
            # ---- Step 3: Process V2 results (V2 only, no V1) ----
            v2_data = v2.get('data', {})

            if v2_data.get('inquiry_questions'):
                # V2 returned symptom list -- save symptoms as the result
                inquiry_qs = v2_data['inquiry_questions']
                symptom_names = [q.get('name', '') for q in inquiry_qs]
                constitution_type = '、'.join(symptom_names[:3]) if symptom_names else '舌诊分析'
                details = {
                    'symptoms': symptom_names,
                    'session_id': v2_data.get('session_id', ''),
                    'inquiry_questions': inquiry_qs
                }
                constitution_details = json.dumps(details, ensure_ascii=False)
                analysis_result = json.dumps(v2_data, ensure_ascii=False)
            elif v2_data.get('report'):
                # Direct report (if API returns answer_type=2 style)
                report = v2_data['report']
                constitution_type = report.get('syndrome_name', '舌诊分析')
                details = {
                    'syndrome_explain': report.get('syndrome_explain', ''),
                    'risk_warning': report.get('risk_warning', ''),
                    'diagnose_key_words': report.get('diagnose_key_words', []),
                    'suggest_food': report.get('suggest_food', ''),
                }
                constitution_details = json.dumps(details, ensure_ascii=False)
                analysis_result = json.dumps(report, ensure_ascii=False)
            else:
                # Fallback: save raw V2 response
                constitution_type = '舌诊分析'
                constitution_details = json.dumps(v2_data, ensure_ascii=False)
                analysis_result = json.dumps(v2, ensure_ascii=False)

            cur.execute("""
                UPDATE tongue_records
                SET analysis_result=%s, constitution_type=%s, constitution_details=%s
                WHERE id=%s
            """, (analysis_result, constitution_type, constitution_details, record_id))
            conn.commit()

            return jsonify({
                'success': True,
                'constitution_type': constitution_type,
                'constitution_details': constitution_details,
                'analysis_result': analysis_result
            })
    finally:
        conn.close()


def _upload_to_public_host(image_path):
    """Upload image to a public image hosting service and return the public URL."""
    with open(image_path, 'rb') as img_file:
        raw = img_file.read()

    services = [
        _upload_0x0(raw),
        _upload_imgbb(raw),
        _upload_freeimage(raw),
    ]
    for url in services:
        if url:
            return url
    return None


def _upload_0x0(raw):
    r = requests.post('https://0x0.st', files={'file': ('tongue.jpg', raw)}, timeout=30)
    if r.status_code == 200:
        u = r.text.strip()
        return u if u.startswith('http') else None
    return None


def _upload_imgbb(raw):
    b64 = base64.b64encode(raw).decode()
    r = requests.post('https://api.imgbb.com/1/upload',
                      data={'key': IMG_HOST_IMGBB_KEY, 'image': b64},
                      timeout=30)
    if r.status_code == 200:
        return r.json().get('data', {}).get('url')
    return None


def _upload_freeimage(raw):
    r = requests.post('https://freeimage.host/api/1/upload',
                      data={'key': IMG_HOST_FREEIMAGE_KEY},
                      files={'source': ('tongue.jpg', raw)},
                      timeout=30)
    if r.status_code == 200:
        d = r.json()
        return d.get('image', {}).get('url') or d.get('image', {}).get('display_url')
    return None
