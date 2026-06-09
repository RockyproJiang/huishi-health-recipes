from flask import Blueprint, request, jsonify, session
from datetime import date
from models.database import get_db, login_required
from config import get_ai_client
from data.health_recipes import HEALTH_RECIPES

health_bp = Blueprint('health', __name__)

MAX_HISTORY = 50  # 每个用户最多保留最近 50 条对话

SYSTEM_PROMPT = """
        以下是完整的系统提示词，已将所有数据原样纳入，不省略任何内容，且不使用任何markdown符号。

你是慧食图谱的AI营养助手。你的回答必须专业、亲切、简洁。禁止使用任何markdown符号（如#、*、`、```、>等），但可以通过换行、缩进、数字编号等方式保持清晰结构。

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

六、输出格式限制
- 禁止使用任何markdown符号，包括但不限于：# * - > ` ``` [ ] ( ) 等特殊符号（数学符号及正常标点除外）。
- 不要输出代码块、JSON、XML或任何标记语言。
- 用自然语言分段和分行，保持可读性即可。
- 可以礼貌使用emoji（如🍎🥦💪），但不能替代文字说明。

以上为完整知识库。现在请以慧食图谱AI营养助手的身份，遵循所有规则，与用户进行交互。
        """


def _build_profile_text(user_id):
    conn = None
    try:
        conn = get_db()
        profile = {}
        diseases = []
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
    except Exception:
        return "\n【当前用户健康档案】无法读取健康数据。\n"
    finally:
        if conn:
            conn.close()

    has_profile = any([profile.get("height"), profile.get("weight"), profile.get("age")])
    if has_profile:
        parts = []
        if profile.get("height"): parts.append(f'身高{profile["height"]}cm')
        if profile.get("weight"): parts.append(f'体重{profile["weight"]}kg')
        if profile.get("age"): parts.append(f'年龄{profile["age"]}岁')
        if profile.get("gender"): parts.append(f'性别{profile["gender"]}')
        if profile.get("plan_tag"): parts.append(f'健康标签：{profile["plan_tag"]}')
        text = "，".join(parts)
        if diseases:
            disease_str = "、".join([d["disease"] for d in diseases])
            text += f"。既往病史：{disease_str}"
        return f"\n【当前用户健康档案】{text}\n请在后续对话中始终基于以上档案数据提供个性化建议。"
    else:
        return "\n【当前用户健康档案】用户尚未填写身高、体重、年龄等基本信息。请在首次回复中友好地引导用户到「个人中心」填写健康档案，以便提供精准的营养建议。\n"


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
        print("AI 调用错误：", e)
        return jsonify({'error': 'AI 服务暂时不可用，请稍后重试'}), 500

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

