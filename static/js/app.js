        let currentUser = null;
        let dailyMeals = { breakfast: null, lunch: null, dinner: null, health_porridge: null, health_tea: null, health_soup: null, health_dish: null };
        let foodsData = { breakfast: [], lunch: [], dinner: [], categories: [] };
        let waterCount = 0;
        let selectedDiseases = [];
        let currentMealType = '';
        let currentCategory = '全部';
        let waterLastClick = null;
        let countdownInterval = null;
        let calendarYear, calendarMonth;
        let currentHealthRecipeType = 'porridge';
        let currentHealthRecipeData = null;

        const EXERCISE_PLANS = [
    { id: "wuqinxi", name: "五禽戏", desc: "模仿五种动物，强健五脏，舒筋活络", steps: [
        { title: "第一式：虎举", content: "1. 站立，两脚与肩同宽，两臂自然下垂，目视前方。\n2. 双手掌心向下，十指张开，用力抓握成虎爪状（手指用力弯曲）。\n3. 两臂缓缓向上举起，如托举重物，举至头顶上方，同时提踵（脚跟离地）。\n4. 双手在头顶上方完全展开，掌心向上，稍停1-2秒。\n5. 然后十指再次用力抓握，缓缓下落至胸前，再翻掌下按至大腿外侧，脚跟落地。\n6. 一上一下为1次，共做3-5次。\n功效：疏通三焦，增强握力，调理肺气，缓解肩背僵硬。" },
        { title: "第二式：虎扑", content: "1. 站立，两腿微屈，重心移向右腿，左腿向前迈出一小步，脚尖点地成虚步。\n2. 双手向前上方扑出，掌心朝前，目视前方，身体前倾，如虎扑食。\n3. 然后重心后移，双手收回至胸前，含胸收腹。\n4. 左右交替，各做3次。\n功效：强健腰肾，舒展脊柱，增强下肢力量。" },
        { title: "第三式：鹿抵", content: "1. 站立，两脚与肩同宽，双手自然下垂。\n2. 左脚向左前方迈出一步，屈膝成左弓步。\n3. 身体向左转，右臂伸直向左前方推出，掌心向左；左臂屈肘向后上方提，掌心向上，目视右脚跟。\n4. 保持姿势2-3秒，然后还原。左右交替，各做3次。\n功效：强健腰肾，运转腰部，缓解腰背酸痛。" },
        { title: "第四式：鹿奔", content: "1. 站立，左脚向前迈一大步，成左弓步。\n2. 双手握空拳，向前上方冲出，拳心向下，同时身体前倾，目视前方。\n3. 然后重心后移，左腿伸直，脚尖翘起，双手收回至胸前。\n4. 左右交替，各做3次。\n功效：舒展脊柱，增强腿部力量，改善颈椎。" },
        { title: "第五式：熊运", content: "1. 站立，两脚与肩同宽，双手握空拳，置于腹部前方。\n2. 以腰为轴，顺时针方向画圈摇晃身体，带动双拳在腹部做圆周运动。\n3. 顺时针、逆时针各做5-7次。\n功效：调理脾胃，促进消化，缓解腹胀。" },
        { title: "第六式：熊晃", content: "1. 站立，左脚向左前方迈出一步，身体重心左右晃动。\n2. 双臂自然下垂，随身体晃动前后摆动，如熊行走。\n3. 左右各走5-7步。\n功效：活动髋膝关节，增强平衡能力。" },
        { title: "第七式：猿提", content: "1. 站立，两脚与肩同宽，双手十指交叉，掌心向上托至胸前。\n2. 提踵，同时双手向上用力托举，目视手背。\n3. 保持2秒，然后落踵，双手下落。重复3-5次。\n功效：提神醒脑，增强心肺功能。" },
        { title: "第八式：猿摘", content: "1. 站立，左脚向左后方撤一步，成左虚步。\n2. 右手向前上方探出，做摘果状，左手护于腕侧。\n3. 然后收回，左右交替各做3次。\n功效：锻炼上肢协调性，改善反应能力。" },
        { title: "第九式：鸟伸", content: "1. 站立，两脚与肩同宽，双手在腹前交叉，掌心向上。\n2. 吸气，双手向上举至头顶，掌心向前，同时提踵。\n3. 呼气，双手向两侧展开如鸟翼，屈膝下蹲。\n4. 重复3-5次。\n功效：调理肺气，预防感冒，舒展胸廓。" },
        { title: "第十式：鸟飞", content: "1. 站立，左脚向前迈出一步，重心前移。\n2. 双臂侧平举上下摆动，如鸟飞翔，同时膝关节配合屈伸。\n3. 左右交替，各做3次。\n功效：增强平衡感，活动肩关节。" }
    ]},
    { id: "liuzijue", name: "六字诀养生法", desc: "嘘呵呼呬吹嘻，调理五脏六腑", steps: [
        { title: "第一式：嘘（xū）字诀——平肝气", content: "1. 两脚开立，与肩同宽，双手自然放于腰侧，掌心向上。\n2. 深吸一口气，然后缓缓呼气，同时口吐“嘘”字音（不出声或微声），双目圆睁，意念注视肝区。\n3. 双手随呼气向前伸出，掌心向外，然后慢慢收回。\n4. 一呼一吸为1次，共做6次。\n功效：疏肝理气，缓解目赤、烦躁。" },
        { title: "第二式：呵（hē）字诀——补心气", content: "1. 两脚分开，双手在胸前交叉，掌心向外。\n2. 深吸气，呼气时口吐“呵”字，双手从胸前向上托举至头顶，掌心向上。\n3. 然后双手分开，缓缓下落至身体两侧。\n4. 共做6次。\n功效：养心安神，改善心悸、失眠。" },
        { title: "第三式：呼（hū）字诀——培脾气", content: "1. 两脚开立，与肩同宽，双手掌心贴于腹部。\n2. 吸气，双手向外展开；呼气，口吐“呼”字，双手向内合拢，轻轻按压腹部。\n3. 共做6次。\n功效：健脾和胃，缓解消化不良、腹胀。" },
        { title: "第四式：呬（xì）字诀——补肺气", content: "1. 两脚开立，双手在胸前合十。\n2. 吸气，双手分开向后展开，扩胸；呼气，口吐“呬”字，双手向前推出。\n3. 共做6次。\n功效：润肺止咳，预防感冒。" },
        { title: "第五式：吹（chuī）字诀——补肾气", content: "1. 两脚开立，双手抱于丹田前。\n2. 吸气，双手上举至头顶；呼气，口吐“吹”字，双手下按至腰侧，同时屈膝下蹲。\n3. 共做6次。\n功效：强腰补肾，改善腰膝酸软。" },
        { title: "第六式：嘻（xī）字诀——理三焦", content: "1. 两脚开立，双手交叉于腹前。\n2. 吸气，双手上举至头顶，翻掌向上；呼气，口吐“嘻”字，双手从两侧缓缓下落。\n3. 共做6次。\n功效：通调三焦，缓解胸闷、眩晕。" }
    ]},
    { id: "yijinjing", name: "易筋经", desc: "抻筋拔骨，调和气血，强身健体", steps: [
        { title: "第一式：韦驮献杵第一式", content: "1. 站立，两脚与肩同宽，双手自然下垂。\n2. 两臂缓缓向前平举，掌心相对，与肩同高。\n3. 屈肘，双手回收至胸前，合掌（两掌相对，指尖朝上），指尖与下颌平齐。\n4. 目视前方，呼吸自然，保持此姿势约30秒。\n功效：稳定心神，调和气血，增强肩臂柔韧性。" },
        { title: "第二式：韦驮献杵第二式", content: "1. 接上式，两掌分开，掌心向下，两臂水平向两侧伸展，呈一字形。\n2. 翻掌，掌心向上，指尖向外，两臂用力外撑，同时提踵。\n3. 目视前方，保持30秒，然后缓缓落踵，收回手臂。\n功效：疏通手三阴、手三阳经，改善肩周炎。" },
        { title: "第三式：韦驮献杵第三式", content: "1. 接上式，两臂上举至头顶，掌心向上，指尖相对，如托天状。\n2. 用力上撑，同时提踵，目视上方。\n3. 保持30秒，然后缓缓下落。\n功效：调理三焦，增强脊柱伸展力。" },
        { title: "第四式：摘星换斗", content: "1. 站立，左手背贴于腰后，右手掌心向下，缓缓向左上方托举，目视右手。\n2. 保持30秒，换右手。\n功效：调理脾胃，舒展侧腰。" },
        { title: "第五式：倒拽九牛尾", content: "1. 左脚向前迈出成弓步，双手握拳，左拳在前，右拳在后，如拽牛尾。\n2. 身体前倾，双臂用力向后拉，保持30秒，换右侧。\n功效：增强臂力和腰力。" },
        { title: "第六式：出爪亮翅", content: "1. 两脚开立，双手收于胸前，掌心向前。\n2. 缓缓向前推出，同时瞪目，保持30秒，然后收回。\n功效：增强肺活量，改善视力。" },
        { title: "第七式：九鬼拔马刀", content: "1. 站立，左手绕至背后，掌心贴背；右手绕至头后，掌心贴左耳。\n2. 身体向右转，保持30秒，换另一侧。\n功效：疏通膀胱经，缓解肩背僵硬。" },
        { title: "第八式：三盘落地", content: "1. 两脚开立，屈膝下蹲成马步，双手按于膝盖，手心朝下。\n2. 保持30秒，起身。\n功效：稳固下盘，强健腿部。" },
        { title: "第九式：青龙探爪", content: "1. 站立，左手握拳置于腰侧，右手向左前方探出，弯腰，目视手。\n2. 换右侧。\n功效：疏肝理气，活动腰部。" },
        { title: "第十式：卧虎扑食", content: "1. 左脚向前迈出成弓步，双手撑地，身体前倾如虎扑。\n2. 保持30秒，换右侧。\n功效：强健腰肾，拉伸脊柱。" },
        { title: "第十一式：打躬势", content: "1. 站立，双手十指交叉抱于后脑，身体向前弯腰至90度，保持30秒。\n2. 起身。\n功效：缓解颈椎、腰椎疲劳。" },
        { title: "第十二式：掉尾势", content: "1. 站立，双手交叉，身体左右摆动，同时扭动臀部，如鱼摆尾。\n2. 做7次。\n功效：放松全身关节。" }
    ]},
    { id: "taichi", name: "简化太极拳", desc: "启动气机，活动腰胯，全套简化太极拳核心八式", steps: [
        { title: "第一式：起势", content: "1. 站立，两脚与肩同宽，身体中正，双臂自然下垂。\n2. 慢慢提起双臂至与肩同高，掌心向下，指尖向前。\n3. 屈膝下蹲，同时双掌下按至腹前，目视前方。\n4. 一上一下为1次，重复3次。\n功效：放松肩颈，启动气机，平稳心绪。" },
        { title: "第二式：野马分鬃（左式举例）", content: "1. 接起势，重心移向右腿，左脚向左前方迈出一步，成左弓步。\n2. 左掌向上向左前方划弧，托至眼高，掌心向上；右掌向下向右后方按至胯旁，掌心向下。\n3. 目视左手指尖，身体保持中正，稍停2秒。\n4. 重心后移，收回左脚，换右侧做相同动作。\n5. 左右各做3次。\n功效：活动腰胯，疏通肝胆经，改善下肢协调性。" },
        { title: "第三式：白鹤亮翅", content: "1. 接上式，右脚向前上半步，双手在胸前合抱。\n2. 重心后移成右虚步，右手向上提至额前，左手向下按至左胯旁，如白鹤亮翅。\n3. 保持2秒，左右各做3次。\n功效：舒展胸廓，增强平衡感。" },
        { title: "第四式：搂膝拗步", content: "1. 左脚向前迈出成左弓步，左手搂膝，右手向前推掌。\n2. 左右交替各做3次。\n功效：活动膝关节，锻炼手臂力量。" },
        { title: "第五式：手挥琵琶", content: "1. 右脚跟进半步，成左虚步，左手向上提至胸前，右手下落至左手肘旁，如抱琵琶。\n2. 左右各做3次。\n功效：练习虚步，放松肩臂。" },
        { title: "第六式：倒卷肱", content: "1. 右脚后退一步，右手向后上方画弧，左手向前推掌。\n2. 左右交替后退各3次。\n功效：增强下肢力量和身体协调性。" },
        { title: "第七式：揽雀尾", content: "1. 包含掤、捋、挤、按四法：右脚上前成右弓步，右手前臂掤出；然后身体左转，双手捋回；再向前挤出；最后双手下按。\n2. 左右各做1次。\n功效：综合锻炼腰腿和手臂，培养内劲。" },
        { title: "第八式：十字手", content: "1. 收脚站立，双手在胸前交叉成十字，掌心向内。\n2. 保持3秒，然后缓缓分掌下落，还原起势。\n功效：收势养气，平复心绪。" }
    ]},
    { id: "jingang", name: "八部金刚功", desc: "双手插顶利三焦，手足前后固肾腰，调理脾肤需单举，左肝右肺如射雕，回头望足去心疾，五劳七伤向后瞧，凤凰展翅周身力，两足顿顿饮嗜消", steps: [
        { title: "第一式：双手插顶利三焦", content: "1. 站立，两脚与肩同宽，双手自然下垂，五指并拢。\n2. 双手掌心向上，从身体两侧缓缓上举至头顶，过程中十指用力分开。\n3. 举到头顶时，双手翻掌，掌心向上，指尖相对，用力向上插顶，同时提踵。\n4. 稍停2秒，然后双手分开，从两侧缓缓下落，脚跟落地。\n5. 一上一下为1次，共做5-7次。\n功效：调理三焦，通利全身气机，增强免疫力。" },
        { title: "第二式：手足前后固肾腰", content: "1. 站立，左脚向前迈出成弓步，双手握拳置于腰侧。\n2. 左拳变掌向前推出，右拳变掌向后推出，同时目视前方。\n3. 然后双手收回，换右弓步重复。各做5次。\n功效：强腰固肾，缓解腰背痛。" },
        { title: "第三式：调理脾肤需单举", content: "1. 站立，双手掌心向上，左手向上托举，右手向下按压。\n2. 上下用力对拉，保持3秒，然后交换。\n3. 左右各做5次。\n功效：调理脾胃，增强消化功能。" },
        { title: "第四式：左肝右肺如射雕", content: "1. 左脚向左跨出成马步，左手向左伸直，右手拉弓状，目视左手。\n2. 左右各做5次。\n功效：疏肝理肺，改善胸闷。" },
        { title: "第五式：回头望足去心疾", content: "1. 左脚向前迈出，身体前倾，右手向后下方探，回头望右脚跟。\n2. 左右各做5次。\n功效：调养心脏，缓解心悸。" },
        { title: "第六式：五劳七伤向后瞧", content: "1. 站立，双手叉腰，头慢慢向左后转，目视后方，保持3秒。\n2. 回正，再向右后转。左右各做5次。\n功效：消除五劳七伤，缓解颈椎疲劳。" },
        { title: "第七式：凤凰展翅周身力", content: "1. 两脚开立，双臂向两侧伸展，上下摆动如凤凰展翅，同时屈膝下蹲再起立。\n2. 重复7次。\n功效：活动全身关节，增强柔韧性。" },
        { title: "第八式：两足顿顿饮嗜消", content: "1. 站立，双脚并拢，双手自然下垂，脚跟提起再用力落下，震动全身。\n2. 重复7次。\n功效：消除饮食积滞，促进代谢。" }
    ]},
    { id: "yoga_sun", name: "瑜伽拜日式", desc: "十二式串联，增强柔韧", steps: [
        { title: "拜日式十二式串联", content: "1. 祈祷式：站立，双脚并拢，双手胸前合十，闭目调息。\n2. 举臂式：吸气，双手向上举过头顶，掌心向前，身体微微后仰。\n3. 站立前屈：呼气，弯腰向前向下，双手放于脚两侧（可屈膝）。\n4. 骑马式（右）：吸气，右腿向后撤一大步，膝盖着地，抬头挺胸。\n5. 平板式：呼气，左腿向后撤，与右腿并拢，身体成一条直线。\n6. 八体投地：屈膝、屈肘，胸部、下巴着地，臀部抬高。\n7. 眼镜蛇式：吸气，身体向前滑行，抬头挺胸，伸直手臂（可微屈肘）。\n8. 下犬式：呼气，提臀向上，身体呈倒V形，脚跟尽量踩地。\n9. 骑马式（左）：吸气，左腿向前迈至双手之间，右腿膝盖着地。\n10. 站立前屈：呼气，右腿向前并拢，重复第3式。\n11. 举臂式：吸气，双臂带动身体向上，微微后仰。\n12. 祈祷式：呼气，双手合十回胸前，还原站立。\n功效：活动全身关节，增强柔韧性与血液循环，缓解压力。" }
    ]},
    { id: "zhanzhuang", name: "站桩功", desc: "培补元气，稳固下盘", steps: [
        { title: "第一式：浑圆桩", content: "1. 两脚开立，与肩同宽，脚尖朝前，膝盖微屈（不超过脚尖）。\n2. 臀部如坐高凳，尾闾内收，腰背挺直。\n3. 双手缓缓抬起，环抱于胸前，如抱一气球，掌心向内，十指相对，间距约20厘米。\n4. 沉肩坠肘，手腕放松，目视前方或闭目，舌尖轻抵上颚。\n5. 自然呼吸，意念集中于丹田（小腹）。初练每次站5-10分钟，逐渐延长。\n功效：培补元气，稳固下盘，改善失眠、神经衰弱。" },
        { title: "第二式：马步桩", content: "1. 两脚开立，比肩略宽，屈膝下蹲至大腿与地面平行（或根据体力调整）。\n2. 双手握拳收于腰侧，或前平举。\n3. 保持姿势30秒至1分钟，逐渐延长。\n功效：增强腿部力量，稳固根基。" },
        { title: "第三式：无极桩", content: "1. 两脚并拢，身体自然直立，双手自然下垂。\n2. 全身放松，意念虚空，自然呼吸。\n3. 站5-10分钟。\n功效：放松身心，回归先天状态。" }
    ]},
    { id: "shierduanjin", name: "十二段锦", desc: "宁心安神，固齿生津，全套十二式", steps: [
        { title: "第一式：冥心握固", content: "1. 盘腿坐于垫上（或端坐于椅上），双手握固（大拇指抵住无名指根，其余四指包住拇指）。\n2. 闭目，排除杂念，舌抵上颚，意守丹田，深呼吸9次。\n功效：宁心安神，收敛精气。" },
        { title: "第二式：叩齿集神", content: "1. 接上式，保持握固，上下牙齿轻轻相叩36次，发出清脆声响。\n2. 叩齿后，用舌头在口腔内顺时针搅动9次，再逆时针9次，待唾液满口，分三口咽下，意送丹田。\n功效：固齿生津，滋养肾精，增强消化功能。" },
        { title: "第三式：微摇天柱", content: "1. 盘坐，双手叉腰，头部慢慢向左、右转动，各9次。\n功效：缓解颈椎僵硬，清醒头脑。" },
        { title: "第四式：赤龙搅海", content: "1. 用舌头在口腔内上下左右搅动，产生唾液后分次咽下。\n2. 做36次搅动。\n功效：生津润喉，助消化。" },
        { title: "第五式：摩运肾堂", content: "1. 双手搓热，掌心贴于后腰肾区，上下摩擦至发热。\n2. 做36次。\n功效：强肾壮腰。" },
        { title: "第六式：单双关辘轳", content: "1. 双手握空拳，如摇辘轳，先单臂后双臂，正反各24次。\n功效：活动肩关节，疏通经络。" },
        { title: "第七式：托天按顶", content: "1. 双手交叉上举过头顶，掌心向上，如托天，保持3秒；然后翻掌下按至头顶，掌心向下。\n2. 重复9次。\n功效：调理三焦，缓解肩背。" },
        { title: "第八式：钩攀", content: "1. 盘坐，双脚前伸，双手勾住脚掌，身体前俯。\n2. 保持5秒，重复9次。\n功效：拉伸膀胱经，增强柔韧。" },
        { title: "第九式：波浪鼓", content: "1. 双手抱头，左右摇摆如波浪鼓，做9次。\n功效：放松颈部。" },
        { title: "第十式：摆身", content: "1. 盘坐，身体左右摆动，带动双臂自然甩动，做9次。\n功效：放松腰背。" },
        { title: "第十一式：按膝", content: "1. 双手按于膝盖，顺时针、逆时针揉膝各9次。\n功效：养护膝关节。" },
        { title: "第十二式：舒足", content: "1. 伸直双腿，脚尖回勾，再向前伸展，做9次。\n功效：放松腿部。" }
    ]},
    { id: "daojia", name: "道家养生功", desc: "鸣天鼓+干洗脸+揉耳轮+擦涌泉+叩齿+咽津，醒脑养颜，延年益寿", steps: [
        { title: "第一式：鸣天鼓", content: "1. 坐或站立，双手掌心捂住双耳，手指置于后脑勺。\n2. 用食指压在中指上，然后向下弹拨后脑枕骨处（风池穴附近），发出“咚咚”声，如击鼓。\n3. 连续弹拨36次。\n功效：醒脑开窍，缓解耳鸣、头晕。" },
        { title: "第二式：干洗脸", content: "1. 双手掌心相对快速摩擦至发热。\n2. 用温热的掌心从下往上搓擦面部，先搓额头，再向两侧到面颊，最后到下巴。\n3. 反复搓擦36次，至面部微红发热。\n功效：美容养颜，改善面部血液循环，预防感冒。" },
        { title: "第三式：揉耳轮", content: "1. 用双手拇指和食指捏住耳轮，从上到下揉搓，至耳廓发热。\n2. 做36次。\n功效：补肾强身，改善听力。" },
        { title: "第四式：擦涌泉", content: "1. 盘坐，用右手掌心搓擦左脚心（涌泉穴）100次，然后换手搓右脚。\n功效：引火归元，改善失眠、高血压。" },
        { title: "第五式：叩齿", content: "1. 上下牙齿轻轻叩击36次，可结合咽津。\n功效：坚固牙齿，补肾。" },
        { title: "第六式：咽津", content: "1. 舌抵上颚，待唾液满口后分三口咽下，意送至丹田。\n功效：滋润五脏，助消化。" }
    ]},
    { id: "paida", name: "拍打养生操", desc: "全身经络拍打，疏通气血", steps: [
        { title: "全身经络拍打", content: "1. 预备：站立，双脚与肩同宽，全身放松。\n2. 拍打上肢：右手空掌（五指并拢微屈）从左肩开始，沿手臂外侧（大肠经）向下拍打至手背，再沿内侧（心包经）向上拍回至腋窝。左右交替，各拍3遍。\n3. 拍打下肢：弯腰，双手掌从大腿外侧（胆经）自上而下拍打至脚踝，再从内侧（肝经、脾经）自下而上拍回至腹股沟。左右各3遍。\n4. 拍打背部：双手握拳，拳背或空掌拍打后背部脊柱两侧（膀胱经），从肩胛骨处向下至腰骶部，再向上返回，共3遍。\n5. 拍打腹部：双手掌心轻轻拍打腹部，顺时针方向绕肚脐拍打36圈。\n6. 收式：搓热双手，摩面、摩腰各9次。\n功效：疏通全身经络，促进气血运行，缓解肌肉酸痛，排解毒素。" }
    ]}
];

// 根据餐别和食物名称生成图片URL（早午晚餐）
function getFoodImageUrl(foodName, mealType) {
    const folderMap = {
        breakfast: '早餐',
        lunch: '午餐',
        dinner: '晚餐'
    };
    const folder = folderMap[mealType];
    if (!folder) return '/static/images/breakfast.png';
    // 文件名可能与食物名称不完全一致，这里进行简单替换（如将“/”替换为“ ”）
    let fileName = foodName.replace(/[\\/:*?"<>|]/g, '');
    // 注意：豆浆+油条（半根） 文件名中有空格，保留原样
    return `/static/images/${folder}/${encodeURIComponent(fileName)}.png`;
}

// 根据养生类型和食谱名称生成图片URL
function getHealthRecipeImageUrl(recipeName, recipeType) {
    const folderMap = {
        soup: '汤品类',
        porridge: '粥类',
        dish: '菜品类',
        tea: '茶饮'
    };
    const folder = folderMap[recipeType];
    if (!folder) return '/static/images/y.meal.jpg';
    let fileName = recipeName.replace(/[\\/:*?"<>|]/g, '');
    return `/static/images/${folder}/${encodeURIComponent(fileName)}.png`;
}

        document.addEventListener('DOMContentLoaded', async () => {
            try {
                const resp = await fetch('/check_login');
                const data = await resp.json();
                if (data.logged_in) {
                    currentUser = { id: data.user_id };
                    await loadUserData();
                    document.getElementById('authModal').classList.add('hidden');
                } else {
                    document.getElementById('authModal').classList.remove('hidden');
                }
            } catch (e) { console.error(e); }
            setupAuthEvents();
            initSportModule();
            initDiseaseTags();
            document.getElementById('homeExercise').textContent = localStorage.getItem('exercise_plan') || '暂无';
            updateWaterUI();
        });

        function setupAuthEvents() {
            let isLoginMode = true;
            const submitBtn = document.getElementById('authSubmitBtn');
            const toggleBtn = document.getElementById('toggleAuthMode');
            submitBtn.addEventListener('click', async () => {
                const username = document.getElementById('authUsername').value.trim();
                const password = document.getElementById('authPassword').value.trim();
                if (!username || !password) return alert('请填写完整');
                const url = isLoginMode ? '/login' : '/register';
                try {
                    const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username, password }) });
                    const data = await res.json();
                    if (data.error) { alert(data.error); return; }
                    if (isLoginMode) {
                        currentUser = { id: data.user_id };
                        await loadUserData();
                        document.getElementById('authModal').classList.add('hidden');
                    } else {
                        alert('注册成功，请登录');
                        toggleAuthMode();
                    }
                } catch (e) { alert('网络错误'); }
            });

            function toggleAuthMode() {
                isLoginMode = !isLoginMode;
                document.getElementById('authTitle').textContent = isLoginMode ? '登录' : '注册';
                submitBtn.textContent = isLoginMode ? '登录' : '注册';
                toggleBtn.innerHTML = isLoginMode ? '没有账号？去注册' : '已有账号？去登录';
            }
            toggleBtn.addEventListener('click', toggleAuthMode);
        }

        async function loadUserData() {
            try {
                const res = await fetch('/user_info');
                const d = await res.json();
                currentUser.username = d.username;
                document.getElementById('homePoints').textContent = d.points;
                document.getElementById('profilePoints').textContent = d.points;
                document.getElementById('profileUsername').textContent = d.username;
                document.getElementById('settingsUsername').textContent = d.username;
                if (d.avatar && d.avatar !== 'default.png') {
                    document.getElementById('homeAvatarImg').src = '/static/uploads/' + d.avatar;
                    document.getElementById('profileAvatarImg').src = '/static/uploads/' + d.avatar;
                }
                if (d.profile) {
                    document.getElementById('profileHealthSummary').innerHTML =
                        `身高${d.profile.height||'?'}cm · 体重${d.profile.weight||'?'}kg · ${d.profile.age||'?'}岁 · ${d.profile.gender||'未知'}`;
                    document.getElementById('planDetails').innerHTML = `目标: 减脂控糖 · 偏好: 少油`;
                }
                const mealRes = await fetch('/get_daily_meals');
                const meals = await mealRes.json();
                dailyMeals = { breakfast: null, lunch: null, dinner: null, health_porridge: null, health_tea: null, health_soup: null, health_dish: null };
                if (meals.meals) {
                    meals.meals.forEach(m => {
                        dailyMeals[m.meal_type] = { name: m.food_name, calories: m.calories, price: m.price, protein: m.protein, carbs: m.carbs };
                    });
                }
                updateMealDisplay();
                const foodRes = await fetch('/foods');
                foodsData = await foodRes.json();
                const waterRes = await fetch('/get_water_count');
                waterCount = (await waterRes.json()).count || 0;
                updateWaterUI();
                if (d.medical_history) { selectedDiseases = d.medical_history; }
            } catch (e) { console.error(e); alert('加载用户数据失败'); throw e; }
        }

        function updateWaterUI() {
            const ml = waterCount * 200;
            document.getElementById('waterProgress').style.width = Math.min(100, (waterCount / 8) * 100) + '%';
            document.getElementById('homeWater').textContent = `${waterCount}/8 杯 (${ml}ml)`;
            document.getElementById('waterDisplay').textContent = `${waterCount}/8 杯 (${ml}ml)`;
            updateWaterCountdown();
        }

        function updateWaterCountdown() {
            const now = Date.now();
            const cooldown = 3600;
            const btn = document.getElementById('waterCheckinBtn');
            const span = document.getElementById('waterCountdown');
            if (waterLastClick && (now - waterLastClick) < cooldown * 1000) {
                const remaining = cooldown - Math.floor((now - waterLastClick) / 1000);
                const mins = Math.floor(remaining / 60);
                const secs = remaining % 60;
                span.textContent = `${mins}:${secs.toString().padStart(2,'0')}后可打卡`;
                btn.disabled = true;
                btn.style.opacity = '0.6';
                if (!countdownInterval) {
                    countdownInterval = setInterval(() => {
                        if (waterLastClick && Date.now() - waterLastClick >= cooldown * 1000) {
                            clearInterval(countdownInterval);
                            countdownInterval = null;
                            span.textContent = '';
                            btn.disabled = false;
                            btn.style.opacity = '1';
                        } else updateWaterCountdown();
                    }, 1000);
                }
            } else {
                span.textContent = '';
                btn.disabled = false;
                btn.style.opacity = '1';
                if (countdownInterval) { clearInterval(countdownInterval); countdownInterval = null; }
            }
        }

        function updateMealDisplay() {
            let totalCal = 0;
            ['breakfast', 'lunch', 'dinner'].forEach(t => {
                const m = dailyMeals[t];
                const nameSpan = document.getElementById(`${t}Name`);
                const kcalSpan = document.getElementById(`${t}Kcal`);
                const imgElement = document.querySelector(`#dietBlendCard .meal-item[onclick="openDishCategory('${t}')"] img`);
                if (m) {
                    nameSpan.textContent = m.name;
                    kcalSpan.textContent = `${m.calories} kcal`;
                    totalCal += m.calories;
                    if (imgElement) {
                        imgElement.src = getFoodImageUrl(m.name, t);
                        imgElement.onerror = function() { this.src = `/static/images/${t}.png`; };
                    }
                } else {
                    nameSpan.textContent = '未选择';
                    kcalSpan.textContent = '-';
                    if (imgElement) imgElement.src = `/static/images/${t}.png`;
                }
            });
            for (let key of ['health_porridge', 'health_tea', 'health_soup', 'health_dish']) {
                if (dailyMeals[key]) totalCal += dailyMeals[key].calories;
            }
            document.getElementById('totalCalories').textContent = totalCal + ' kcal';
            const progress = document.getElementById('calorieProgress');
            const target = 2000;
            let percent = Math.min(100, (totalCal / target) * 100);
            progress.style.width = percent + '%';
        }       

        function openDishCategory(mealType) {
            currentMealType = mealType;
            document.getElementById('dishCategoryTitle').textContent = mealType === 'breakfast' ? '早餐' : (mealType === 'lunch' ? '午餐' : '晚餐');
            switchToPage('dishCategoryPage');
            renderCategories();
            renderDishList();
        }

        function renderCategories() {
            const container = document.getElementById('categoryTags');
            container.innerHTML = '';
            const allCats = ['全部', ...new Set(foodsData[currentMealType]?.map(f => f.category) || [])];
            allCats.forEach(cat => {
                const tag = document.createElement('span');
                tag.className = 'category-tag';
                if (cat === currentCategory) tag.classList.add('active');
                tag.textContent = cat;
                tag.onclick = () => { currentCategory = cat; renderCategories(); renderDishList(); };
                container.appendChild(tag);
            });
        }


        function renderDishList() {
            const list = document.getElementById('dishList');
            list.innerHTML = '';
            const allFoods = foodsData[currentMealType] || [];
            const filtered = currentCategory === '全部' ? allFoods : allFoods.filter(f => f.category === currentCategory);
            filtered.forEach(f => {
                const card = document.createElement('div');
                card.className = 'dish-card';
                const imgSrc = getFoodImageUrl(f.name, currentMealType);
                card.innerHTML = `<img src="${imgSrc}" style="width:100%; height:80px; object-fit:cover; border-radius:12px;" onerror="this.src='/static/images/${currentMealType}.png'"><div>${f.name}</div><small>${f.calories}kcal</small>`;
                card.onclick = () => showSingleDish(f);
                list.appendChild(card);
            });
        }

        function showSingleDish(food) {
            window.currentSingleFood = food;
            document.getElementById('dishDetailImg').src = getFoodImageUrl(food.name, currentMealType);
            document.getElementById('dishDetailImg').onerror = function() {
                this.src = `/static/images/${currentMealType}.png`;
            };
            document.getElementById('dishDetailName').textContent = food.name;
            const ingr = food.ingredients?.map(i => `${i.name} ¥${i.price}(${i.quantity})`).join(' | ') || '无';
            document.getElementById('dishDetailIngredients').textContent = `原料: ${ingr} | 价格: ¥${food.price}`;
            document.getElementById('selectDishBtn').onclick = () => selectDish(food);
            switchToPage('singleDishPage');
            setTimeout(() => {
                const chartDom = document.getElementById('dishChart');
                if (chartDom && window.echarts) {
                    const myChart = echarts.init(chartDom);
                    myChart.setOption({
                        backgroundColor: 'transparent',
                        tooltip: {},
                        xAxis: { data: ['热量(kcal)', '蛋白质(g)', '碳水(g)'], axisLine: { lineStyle: { color: '#8B6F4E' } }, axisLabel: { color: '#4A3728' } },
                        yAxis: { axisLine: { lineStyle: { color: '#8B6F4E' } }, splitLine: { lineStyle: { color: '#E8DFD0' } } },
                        series: [{ type: 'bar', data: [food.calories, food.protein, food.carbs], itemStyle: { color: '#8B6F4E' } }]
                    });
                }
            }, 200);
        }

        function selectDish(food) {
            dailyMeals[currentMealType] = { name: food.name, calories: food.calories, price: food.price, protein: food.protein, carbs: food.carbs };
            fetch('/save_meals', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(dailyMeals) });
            updateMealDisplay();
            switchToPage('homePage');
        }

        function backToDishList() {
            switchToPage('dishCategoryPage');
            renderDishList();
        }

        function switchToPage(pageId) {
            document.querySelectorAll('.page-view').forEach(p => p.classList.remove('active'));
            document.getElementById(pageId)?.classList.add('active');
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            const nav = document.querySelector(`.nav-item[data-page="${pageId}"]`);
            if (nav) nav.classList.add('active');
            window.scrollTo({ top: 0, behavior: 'smooth' });
            if (pageId === 'nutritionPage') renderNutritionChart();
            if (pageId === 'ordersPage') loadOrders();
            if (pageId === 'dishCategoryPage') { renderCategories(); renderDishList(); }
            if (pageId === 'homePage') updateMealDisplay();
            if (pageId === 'healthRecipeListPage') loadHealthRecipes();
            if (pageId === 'sportPage') initSportModule();
        }

        async function renderNutritionChart() {
            const res = await fetch('/get_daily_nutrition');
            const d = await res.json();
            const chartDom = document.getElementById('nutritionChart');
            if (chartDom && echarts) {
                if (window.nutritionChartInstance) window.nutritionChartInstance.dispose();
                const myChart = echarts.init(chartDom);
                myChart.setOption({
                    backgroundColor: 'transparent',
                    title: { text: '今日营养与运动', textStyle: { color: '#8B6F4E' } },
                    tooltip: {},
                    xAxis: { data: ['热量(kcal)', '蛋白质(g)', '碳水(g)', '饮水(杯)', '运动(kcal)'], axisLabel: { color: '#4A3728' } },
                    yAxis: { axisLabel: { color: '#4A3728' } },
                    series: [{ type: 'bar', data: [d.total_calories, d.total_protein, d.total_carbs, d.water_cups, d.exercise_calories], itemStyle: { color: '#8B6F4E' } }]
                });
                window.nutritionChartInstance = myChart;
            }
        }

        function generateCart() {
            let items = [], total = 0;
            ['breakfast', 'lunch', 'dinner'].forEach(t => { if (dailyMeals[t]) { items.push(dailyMeals[t]); total += dailyMeals[t].price; } });
            ['health_porridge', 'health_tea', 'health_soup', 'health_dish'].forEach(t => { if (dailyMeals[t]) { items.push(dailyMeals[t]); total += dailyMeals[t].price; } });
            if (!items.length) return alert('请至少选择一餐或养生食谱');
            document.getElementById('cartItems').innerHTML = items.map(m => `<div>${m.name} ¥${m.price}</div>`).join('');
            document.getElementById('cartTotal').textContent = `总价: ¥${total.toFixed(1)}`;
            document.getElementById('cartModal').classList.remove('hidden');
        }

        function payOrder() {
            document.getElementById('cartModal').classList.add('hidden');
            document.getElementById('payModal').classList.remove('hidden');
        }

        function confirmPay() {
            const pwd = document.getElementById('payPassword').value;
            if (pwd.length !== 6 || !/^\d{6}$/.test(pwd)) return alert('请输入六位数字密码');
            alert('支付成功！(模拟)');
            document.getElementById('payModal').classList.add('hidden');
            if (dailyMeals.breakfast) checkin('breakfast', '早餐打卡');
            if (dailyMeals.lunch) checkin('lunch', '午餐打卡');
            if (dailyMeals.dinner) checkin('dinner', '晚餐打卡');
        }

        async function checkin(type, detail) {
            const res = await fetch('/checkin', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type, detail }) });
            const d = await res.json();
            if (d.success) { alert(`打卡成功！+${d.points_added}积分`); loadUserData(); }
            else alert(d.error || '打卡失败');
        }

        async function waterCheckin() {
            const now = Date.now();
            if (waterLastClick && (now - waterLastClick) < 3600 * 1000) return alert('请等待冷却时间结束');
            if (waterCount >= 8) return alert('今日饮水已满');
            await checkin('water', '饮水1杯');
            waterCount++;
            waterLastClick = now;
            updateWaterUI();
        }

        async function applyPlan(tag) {
            await fetch('/save_profile', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ plan_tag: tag }) });
            document.getElementById('planGroupView').style.display = 'none';
            document.getElementById('planCustomView').style.display = 'block';
            alert(`已应用"${tag}"方案`);
            loadUserData();
            appendChatBubble('ai', `方案已更新为"${tag}"，有什么可以帮您？`);
        }

        function backToGroupPlan() {
            document.getElementById('planGroupView').style.display = 'block';
            document.getElementById('planCustomView').style.display = 'none';
        }

        async function sendChatPlan() {
            const input = document.getElementById('chatInputPlan');
            const msg = input.value.trim();
            if (!msg) return;
            appendChatBubble('user', msg);
            input.value = '';
            const chatBox = document.getElementById('chatBoxPlan');
            const typing = document.createElement('div');
            typing.className = 'chat-typing';
            typing.innerHTML = '<span></span><span></span><span></span>';
            chatBox.appendChild(typing);
            try {
                const res = await fetch('/ai_chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: msg }) });
                const d = await res.json();
                typing.remove();
                appendChatBubble('ai', d.reply || 'AI暂时无响应');
            } catch (e) { typing.remove(); appendChatBubble('ai', '网络错误'); }
        }

        function appendChatBubble(role, text) {
            const box = document.getElementById('chatBoxPlan');
            const div = document.createElement('div');
            div.className = `chat-bubble ${role}`;
            div.textContent = text;
            box.appendChild(div);
            box.scrollTop = box.scrollHeight;
        }

        function openTongueModal() {
            document.getElementById('tongueModal').classList.remove('hidden');
            const video = document.getElementById('tongueVideo');
            navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } })
                .then(stream => { video.srcObject = stream; video.play(); })
                .catch(() => alert('无法访问摄像头'));
        }

        function closeTongueModal() {
            const video = document.getElementById('tongueVideo');
            if (video.srcObject) { video.srcObject.getTracks().forEach(t => t.stop()); video.srcObject = null; }
            document.getElementById('tongueModal').classList.add('hidden');
        }

        function captureTongue() {
            const video = document.getElementById('tongueVideo');
            const canvas = document.getElementById('tongueCanvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            alert('拍照成功（舌诊分析功能暂未开放）');
        }

        function setHealthRecipeType(type) {
            currentHealthRecipeType = type;
            const titles = { 'soup': '养生汤', 'porridge': '养生粥', 'dish': '养生菜', 'tea': '养生茶' };
            document.getElementById('healthRecipeListTitle').textContent = titles[type] || '养生食谱';
        }

        async function loadHealthRecipes() {
            const res = await fetch('/health_recipes');
            const data = await res.json();
            const recipes = data[currentHealthRecipeType] || [];
            const grid = document.getElementById('healthRecipeGrid');
            grid.innerHTML = '';
            recipes.forEach(recipe => {
                const card = document.createElement('div');
                card.className = 'dish-card';
                const imgSrc = getHealthRecipeImageUrl(recipe.name, currentHealthRecipeType);
                card.innerHTML = `<img src="${imgSrc}" style="width:100%; height:80px; object-fit:cover; border-radius:12px;" onerror="this.src='/static/images/y.${currentHealthRecipeType}.jpg'"><div>${recipe.name}</div><small>${recipe.calories}kcal</small>`;
                card.onclick = () => showHealthRecipeDetail(recipe);
                grid.appendChild(card);
            });
        }

        function showHealthRecipeDetail(recipe) {
            currentHealthRecipeData = recipe;
            document.getElementById('healthRecipeDetailImg').src = getHealthRecipeImageUrl(recipe.name, currentHealthRecipeType);
            document.getElementById('healthRecipeDetailImg').onerror = function() {
                this.src = `/static/images/y.${currentHealthRecipeType}.jpg`;
            };
            document.getElementById('healthRecipeDetailName').textContent = recipe.name;
            document.getElementById('healthRecipeIngredients').textContent = `原料：${recipe.ingredients}`;
            document.getElementById('healthRecipeEffect').innerHTML = `<i class="fas fa-heart" style="color:#C75C3A;"></i> 功效：${recipe.effect}`;
            document.getElementById('healthRecipeMethod').innerHTML = `<strong>制作方法：</strong><br>${recipe.method}`;
            document.getElementById('selectHealthRecipeBtn').onclick = () => selectHealthRecipe(recipe);
            switchToPage('healthRecipeDetailPage');
        }

        async function selectHealthRecipe(recipe) {
            const typeMap = { 'porridge': 'health_porridge', 'tea': 'health_tea', 'soup': 'health_soup', 'dish': 'health_dish' };
            const mealType = typeMap[currentHealthRecipeType];
            dailyMeals[mealType] = { name: recipe.name, calories: recipe.calories, price: recipe.price, protein: 0, carbs: 0 };
            await fetch('/save_meal', { method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ meal_type: mealType, food_name: recipe.name, calories: recipe.calories, price: recipe.price }) });
            updateMealDisplay();
            switchToPage('homePage');
        }

        function initSportModule() {
            const SPORTS = [
                { id: "run", name: "跑步", emoji: "🏃‍♂️", ratePerMin: 10.2, img: "s.run.jpg" },
                { id: "bike", name: "骑车", emoji: "🚴‍♀️", ratePerMin: 8.5, img: "s.bike.jpg" },
                { id: "weight", name: "举重", emoji: "🏋️‍♂️", ratePerMin: 6.8, img: "s.weight.jpg" },
                { id: "swim", name: "游泳", emoji: "🏊‍♂️", ratePerMin: 11.5, img: "s.swim.jpg" },
                { id: "yoga", name: "瑜伽", emoji: "🧘‍♀️", ratePerMin: 4.5, img: "s.yoga.jpg" },
                { id: "walk", name: "健走", emoji: "🚶‍♂️", ratePerMin: 5.6, img: "s.walk.jpg" }
            ];

            // 功法图片映射（plan.id -> 图片文件名，请确保图片存在于 /static/images/ 目录）
            const planImageMap = {
                wuqinxi: 'f.animal.jpg',
                liuzijue: 'f.six.jpg',
                yijinjing: 'f.yi.jpg',
                taichi: 'f.taichi.jpg',
                jingang: 'f.eight.jpg',
                zhanzhuang: 'f.stand.jpg',
                yoga_sun: 'f.yoga.jpg',
                shierduanjin: 'f.knock.jpg',
                daojia: 'f.daoeight.jpg',
                paida: 'f.gor.jpg'
            };

            window.activeContext = null;
            let timerInterval = null;
            const container = document.getElementById('sportContainer');
            if (!container) return;

            // 渲染运动页 UI（与原来一致）
            container.innerHTML = `
                <div style="display:flex; gap:8px; margin-bottom:16px;">
                    <div class="sub-tab active" id="modeSportTab">🏃 运动</div>
                    <div class="sub-tab" id="modePlanTab">📋 计划</div>
                </div>
                <div class="sport-grid" id="sportListView"></div>
                <div class="sport-grid" id="planListView" style="display:none;"></div>
                <div id="executionView" style="display:none;" class="info-card">
                    <div style="font-size:3rem; text-align:center;" id="execEmoji"></div>
                    <h2 style="text-align:center; color:#4A3728;" id="execTitle"></h2>
                    <div class="timer-big" id="execTimer">00:00:00</div>
                    <div style="text-align:center; color:#C75C3A;">🔥 <span id="execCalories">0.0</span> kcal</div>
                    <div class="btn-group" style="justify-content:center; margin-top:12px;">
                        <button class="btn-gold" id="startBtn" style="width:auto;">▶ 开始</button>
                        <button class="btn-outline-gold" id="pauseBtn">⏸ 暂停</button>
                        <button class="btn-outline-gold" id="resetBtn">🔄 重置</button>
                    </div>
                    <button class="btn-outline-gold" id="joinPlanBtn" style="width:100%; margin-top:8px;" onclick="window.joinPlan()">➕ 加入计划</button>
                    <button class="btn-outline-gold" id="abortBtn" style="width:100%; margin-top:8px;">退出并保存</button>
                </div>
            `;

            // 1. 运动项卡片（blend-card 带图片）
            const sportGrid = document.getElementById('sportListView');
            SPORTS.forEach(s => {
                const card = document.createElement('div');
                card.className = 'blend-card';
                card.style.cursor = 'pointer';
                card.innerHTML = `
                    <div class="blend-content" style="display:flex; flex-direction:row; align-items:center; gap:14px; padding:16px;">
                        <div style="font-size:2rem;">${s.emoji}</div>
                        <div style="flex:1">
                            <div style="font-weight:700; color:#4A3728;">${s.name}</div>
                            <small style="color:#8C7B6B;">${s.ratePerMin} kcal/分</small>
                        </div>
                    </div>
                    <div class="blend-image-half">
                        <div class="image-blend" style="background-image: url('/static/images/${s.img}');" 
                            onerror="this.classList.add('error-fallback'); this.style.backgroundImage='radial-gradient(circle at 70% 30%, #E8DFD0, #C4A882)';"></div>
                    </div>
                `;
                card.onclick = () => startExercise(s);
                sportGrid.appendChild(card);
            });

            // 2. 运动功法卡片（使用 blend-card 带图片）
            const planGrid = document.getElementById('planListView');
            planGrid.innerHTML = '';
            planGrid.className = 'sport-grid';   // 使用与运动项相同的网格布局
            EXERCISE_PLANS.forEach(plan => {
                const imgFile = planImageMap[plan.id] || 'default_plan.jpg';
                const imgUrl = `/static/images/${imgFile}`;

                const card = document.createElement('div');
                card.className = 'blend-card clickable';
                card.onclick = () => showExerciseDetail(plan);

                // 左侧内容区
                const leftDiv = document.createElement('div');
                leftDiv.className = 'blend-content';
                leftDiv.style.padding = '20px 18px';
                leftDiv.innerHTML = `
                    <div style="font-size: 1.8rem; margin-bottom: 6px;">🧘</div>
                    <div style="font-weight: 700; font-size: 1.1rem; color: #4A3728;">${plan.name}</div>
                    <div style="font-size: 0.75rem; color: #8C7B6B; margin-top: 4px;">${plan.desc}</div>
                `;

                // 右侧图片区（带渐变遮罩）
                const rightDiv = document.createElement('div');
                rightDiv.className = 'blend-image-half';
                const imgDiv = document.createElement('div');
                imgDiv.className = 'image-blend';
                imgDiv.style.backgroundImage = `url('${imgUrl}')`;
                imgDiv.onerror = function() {
                    this.classList.add('error-fallback');
                    this.style.backgroundImage = "radial-gradient(circle at 70% 30%, #E8DFD0, #C4A882)";
                };
                rightDiv.appendChild(imgDiv);

                card.appendChild(leftDiv);
                card.appendChild(rightDiv);
                planGrid.appendChild(card);
            });

            // 3. 标签切换逻辑
            document.getElementById('modeSportTab').onclick = () => {
                document.getElementById('sportListView').style.display = 'grid';
                document.getElementById('planListView').style.display = 'none';
                document.getElementById('modeSportTab').classList.add('active');
                document.getElementById('modePlanTab').classList.remove('active');
            };
            document.getElementById('modePlanTab').onclick = () => {
                document.getElementById('planListView').style.display = 'grid';
                document.getElementById('sportListView').style.display = 'none';
                document.getElementById('modePlanTab').classList.add('active');
                document.getElementById('modeSportTab').classList.remove('active');
            };

            // 4. 运动计时相关函数（保持不变）
            function startExercise(sport) {
                if (timerInterval) clearInterval(timerInterval);
                window.activeContext = { type: 'sport', data: sport, elapsedSeconds: 0, isRunning: false };
                document.getElementById('execEmoji').textContent = sport.emoji;
                document.getElementById('execTitle').textContent = sport.name;
                document.getElementById('sportListView').style.display = 'none';
                document.getElementById('planListView').style.display = 'none';
                document.getElementById('executionView').style.display = 'block';
                updateExec();
            }

            function updateExec() {
                if (!window.activeContext) return;
                const sec = window.activeContext.elapsedSeconds;
                const h = String(Math.floor(sec / 3600)).padStart(2, '0');
                const m = String(Math.floor((sec % 3600) / 60)).padStart(2, '0');
                const s = String(sec % 60).padStart(2, '0');
                document.getElementById('execTimer').textContent = `${h}:${m}:${s}`;
                const kcal = (sec / 60) * window.activeContext.data.ratePerMin;
                document.getElementById('execCalories').textContent = kcal.toFixed(1);
            }

            function startTimer() {
                if (window.activeContext && !window.activeContext.isRunning) {
                    window.activeContext.isRunning = true;
                    timerInterval = setInterval(() => {
                        window.activeContext.elapsedSeconds++;
                        updateExec();
                    }, 1000);
                }
            }

            function pauseTimer() {
                if (window.activeContext) window.activeContext.isRunning = false;
                if (timerInterval) clearInterval(timerInterval);
            }

            function resetTimer() {
                if (window.activeContext) {
                    window.activeContext.elapsedSeconds = 0;
                    updateExec();
                }
            }

            async function abortExercise() {
                if (window.activeContext && window.activeContext.elapsedSeconds > 0) {
                    const cal = (window.activeContext.elapsedSeconds / 60) * window.activeContext.data.ratePerMin;
                    await fetch('/save_exercise', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            type: window.activeContext.type,
                            name: window.activeContext.data.name,
                            duration_seconds: window.activeContext.elapsedSeconds,
                            calories: cal.toFixed(1),
                            award_points: window.activeContext.elapsedSeconds >= 1800
                        })
                    });
                }
                if (timerInterval) clearInterval(timerInterval);
                window.activeContext = null;
                document.getElementById('executionView').style.display = 'none';
                document.getElementById('sportListView').style.display = 'grid';
                document.getElementById('planListView').style.display = 'none';
            }

            // 绑定按钮事件
            document.getElementById('startBtn').onclick = startTimer;
            document.getElementById('pauseBtn').onclick = pauseTimer;
            document.getElementById('resetBtn').onclick = resetTimer;
            document.getElementById('abortBtn').onclick = abortExercise;
        }

        function showExerciseDetail(plan) {
            document.getElementById('exerciseDetailTitle').textContent = plan.name;
            const contentDiv = document.getElementById('exerciseDetailContent');
            contentDiv.innerHTML = '';
            plan.steps.forEach(step => {
                const stepCard = document.createElement('div');
                stepCard.className = 'info-card';
                stepCard.innerHTML = `<h3 style="color:#4A3728;">${step.title}</h3><p style="white-space: pre-line; font-size:0.85rem;">${step.content}</p>`;
                contentDiv.appendChild(stepCard);
            });
            switchToPage('exerciseDetailPage');
        }

        window.joinPlan = function() {
            if (window.activeContext) {
                localStorage.setItem('exercise_plan', window.activeContext.data.name);
                document.getElementById('homeExercise').textContent = window.activeContext.data.name;
                alert(`已将${window.activeContext.data.name}加入运动计划`);
            }
        };

        async function showExerciseRecords() {
            const res = await fetch('/get_exercise_records');
            const data = await res.json();
            let html = '<h3 style="color:#4A3728;">运动记录</h3>';
            if (data.records?.length) {
                html += data.records.map(r => `<div class="info-card">${r.name} · ${Math.floor(r.duration_seconds/60)}分钟 · ${r.calories}kcal · ${r.date}</div>`).join('');
            } else html += '<div class="info-card">暂无记录</div>';
            document.getElementById('exerciseRecordContent').innerHTML = html;
            document.getElementById('exerciseRecordModal').classList.remove('hidden');
        }

        const ALL_DISEASES = ['过敏', '糖尿病', '高血压', '高血脂', '心脏病', '痛风', '乳糖不耐受', '其他'];
        function initDiseaseTags() {
            const container = document.getElementById('diseaseTags');
            if (!container) return;
            container.innerHTML = '';
            ALL_DISEASES.forEach(d => {
                const tag = document.createElement('span');
                tag.className = 'disease-tag';
                tag.textContent = d;
                tag.onclick = () => {
                    tag.classList.toggle('selected');
                    if (tag.classList.contains('selected')) {
                        const detail = prompt(`请输入${d}详情（如过敏原、严重程度），无则留空`);
                        selectedDiseases.push({ disease: d, detail: detail || '' });
                    } else {
                        selectedDiseases = selectedDiseases.filter(i => i.disease !== d);
                    }
                };
                container.appendChild(tag);
            });
        }

        async function saveProfile() { 
            const height = document.getElementById('editHeight').value;
            const weight = document.getElementById('editWeight').value;
            const age = document.getElementById('editAge').value;
            const gender = document.getElementById('editGender').value;
            await fetch('/save_profile', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ height, weight, age, gender, diseases: selectedDiseases }) });
            alert('保存成功');
            switchToPage('profilePage');
            loadUserData();
        }
        async function uploadAvatar() {
            const file = document.getElementById('avatarInput').files[0];
            if (!file) return;
            const formData = new FormData();
            formData.append('avatar', file);
            const res = await fetch('/upload_avatar', { method: 'POST', body: formData });
            const d = await res.json();
            if (d.avatar) document.getElementById('profileAvatarImg').src = '/static/uploads/' + d.avatar;
        }
        function uploadAvatarFromSettings() { document.getElementById('avatarInput').click(); }
        async function changeUsername() { 
            const newName = prompt('输入新用户名');
            if (!newName) return;
            const res = await fetch('/change_username', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ new_username: newName }) });
            const d = await res.json();
            if (d.error) alert(d.error);
            else { alert('用户名修改成功'); loadUserData(); }
        }
        async function changePassword() {
            const oldPw = prompt('输入旧密码');
            if (!oldPw) return;
            const newPw = prompt('输入新密码');
            if (!newPw) return;
            const res = await fetch('/change_password', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ old_password: oldPw, new_password: newPw }) });
            const d = await res.json();
            if (d.error) alert(d.error);
            else alert('密码修改成功，请重新登录');
        }
        async function logout() {
            await fetch('/logout', { method: 'POST' });
            sessionStorage.clear();
            currentUser = null;
            dailyMeals = { breakfast: null, lunch: null, dinner: null, health_porridge: null, health_tea: null, health_soup: null, health_dish: null };
            waterCount = 0;
            updateWaterUI();
            document.getElementById('authModal').classList.remove('hidden');
            setActivePage('homePage');
        }
        async function exchange(item) {
            if (!confirm(`确认兑换${item}？`)) return;
            const res = await fetch('/exchange', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ item }) });
            const d = await res.json();
            if (d.error) alert(d.error);
            else { alert('兑换成功'); loadUserData(); }
        }
        async function loadOrders() {
            const res = await fetch('/get_orders');
            const d = await res.json();
            const ordersDiv = document.getElementById('ordersList');
            if (ordersDiv) ordersDiv.innerHTML = d.orders.map(o => `<div class="info-card">${o.item_name} · ${o.points_cost}积分 · ${o.created_at}</div>`).join('') || '暂无订单';
        }
        function showInfoModal(title) {
            document.getElementById('infoModalTitle').textContent = title;
            document.getElementById('infoModalContent').textContent = '暂无内容';
            document.getElementById('infoModal').classList.remove('hidden');
        }
        async function openCalendar() {
            const now = new Date();
            calendarYear = now.getFullYear();
            calendarMonth = now.getMonth() + 1;
            document.getElementById('calendarFullscreen').classList.add('active');
            await renderCalendar();
        }
        function closeCalendar() {document.getElementById('calendarFullscreen').classList.remove('active');}
        async function renderCalendar() {
            const res = await fetch(`/calendar_data?year=${calendarYear}&month=${calendarMonth}`);
            const data = await res.json();
            const checkedDates = data.checked_dates || [];
            document.getElementById('calendarNav').innerHTML = `
            <button class="nav-btn" onclick="changeMonth(-1)">◀</button>
            <span style="color:#D4AF37; font-size:1.4rem;">${calendarYear}年${calendarMonth}月</span>
            <button class="nav-btn" onclick="changeMonth(1)">▶</button>
        `;
            document.getElementById('calendarWeekdays').innerHTML = ['日', '一', '二', '三', '四', '五', '六'].map(d => `<div>${d}</div>`).join('');
            const firstDay = new Date(calendarYear, calendarMonth - 1, 1).getDay();
            const daysInMonth = new Date(calendarYear, calendarMonth, 0).getDate();
            const today = new Date();
            const todayStr = `${today.getFullYear()}-${(today.getMonth()+1).toString().padStart(2,'0')}-${today.getDate().toString().padStart(2,'0')}`;
            let gridHTML = '';
            for (let i = 0; i < firstDay; i++) gridHTML += '<div class="day-cell other-month"></div>';
            for (let d = 1; d <= daysInMonth; d++) {
                const dateStr = `${calendarYear}-${calendarMonth.toString().padStart(2,'0')}-${d.toString().padStart(2,'0')}`;
                const isToday = dateStr === todayStr;
                const isCompleted = checkedDates.includes(dateStr);
                gridHTML += `<div class="day-cell${isToday?' today':''}${isCompleted?' completed':''}" data-date="${dateStr}" onclick="toggleCalendarDay(this)">${d}</div>`;
            }
            document.getElementById('calGrid').innerHTML = gridHTML;
            const count = checkedDates.length;
            document.getElementById('calStats').innerHTML = `<span>本月打卡 ${count}/${daysInMonth} 天</span>`;
        }
        async function toggleCalendarDay(el) { 
            const date = el.dataset.date;
            const res = await fetch('/toggle_calendar', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ date }) });
            const data = await res.json();
            if (data.success) renderCalendar();
        }
        async function changeMonth(delta) {
            calendarMonth += delta;
            if (calendarMonth > 12) { calendarMonth = 1; calendarYear++; } else if (calendarMonth < 1) { calendarMonth = 12; calendarYear--; }
            renderCalendar();
        }
        function setActivePage(pageId) { switchToPage(pageId); }
