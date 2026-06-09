const { createApp, ref, reactive, computed, watch, onMounted, nextTick } = Vue;

const app = createApp({
    setup() {
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
                { title: "第一式：嘘（xū）字诀——平肝气", content: "1. 两脚开立，与肩同宽，双手放于腰侧。\n2. 深吸气，缓缓呼气吐\"嘘\"字音，双目圆睁。\n3. 双手随呼气向前伸出，掌心向外，然后收回。\n4. 共做6次。\n功效：疏肝理气，缓解目赤、烦躁。" },
                { title: "第二式：呵（hē）字诀——补心气", content: "1. 两脚开立，双手胸前交叉。\n2. 深吸气，呼气吐\"呵\"字，双手上托至头顶。\n3. 双手分开下落。\n4. 共做6次。\n功效：养心安神，改善心悸、失眠。" },
                { title: "第三式：呼（hū）字诀——培脾气", content: "1. 两脚开立，双手贴腹部。\n2. 吸气双手外展，呼气吐\"呼\"字，双手内合按腹。\n3. 共做6次。\n功效：健脾和胃，缓解消化不良。" },
                { title: "第四式：呬（xì）字诀——补肺气", content: "1. 两脚开立，双手胸前合十。\n2. 吸气扩胸，呼气吐\"呬\"字，双手前推。\n3. 共做6次。\n功效：润肺止咳，预防感冒。" },
                { title: "第五式：吹（chuī）字诀——补肾气", content: "1. 两脚开立，双手抱丹田。\n2. 吸气上举，呼气吐\"吹\"字，下按屈膝。\n3. 共做6次。\n功效：强腰补肾，改善腰膝酸软。" },
                { title: "第六式：嘻（xī）字诀——理三焦", content: "1. 两脚开立，双手交叉腹前。\n2. 吸气上举翻掌，呼气吐\"嘻\"字，双手下落。\n3. 共做6次。\n功效：通调三焦，缓解胸闷、眩晕。" }
            ]},
            { id: "yijinjing", name: "易筋经", desc: "抻筋拔骨，调和气血", steps: [
                { title: "第一式：韦驮献杵", content: "1. 站立，两脚与肩同宽。\n2. 两臂向前平举，掌心相对。\n3. 屈肘回收胸前合掌。\n4. 保持30秒。\n功效：稳定心神，调和气血。" },
                { title: "第二式：横担降魔杵", content: "1. 两掌分开，掌心向下。\n2. 两臂水平向两侧伸展。\n3. 翻掌向上，用力外撑，提踵。\n4. 保持30秒。\n功效：疏通经络，改善肩周。" }
            ]}
        ];

        const SPORTS = [
            { id: "run", name: "跑步", emoji: "🏃‍♂️", ratePerMin: 10.2, img: "s.run.jpg" },
            { id: "bike", name: "骑车", emoji: "🚴‍♀️", ratePerMin: 8.5, img: "s.bike.jpg" },
            { id: "weight", name: "举重", emoji: "🏋️‍♂️", ratePerMin: 6.8, img: "s.weight.jpg" },
            { id: "swim", name: "游泳", emoji: "🏊‍♂️", ratePerMin: 11.5, img: "s.swim.jpg" },
            { id: "yoga", name: "瑜伽", emoji: "🧘‍♀️", ratePerMin: 4.5, img: "s.yoga.jpg" },
            { id: "walk", name: "健走", emoji: "🚶‍♂️", ratePerMin: 5.8, img: "s.walk.jpg" }
        ];

        const ALL_DISEASES = ['过敏', '糖尿病', '高血压', '高血脂', '心脏病', '痛风', '乳糖不耐受', '其他'];
        const DISEASE_TAG_CLASS = (d) => selectedDiseases.value.some(i => i.disease === d) ? 'disease-tag selected' : 'disease-tag';
        // ==================== 全局状态 ====================
        const currentUser = ref(null);
        const currentPage = ref('homePage');
        const dailyMeals = reactive({
            breakfast: null, lunch: null, dinner: null,
            health_porridge: null, health_tea: null, health_soup: null, health_dish: null
        });
        const foodsData = reactive({ breakfast: [], lunch: [], dinner: [], categories: [] });
        const waterCount = ref(0);
        const waterLastClick = ref(null);
        const waterCooldown = ref(0);
        let countdownInterval = null;

        // Auth
        const authMode = ref('login');
        const authUsername = ref('');
        const authPassword = ref('');

        // Modals
        const showAuth = ref(true);
        const showNotify = ref(false);
        const showCart = ref(false);
        const showPay = ref(false);
        const showInfo = ref(false);
        const showExerciseRecord = ref(false);
        const showTongue = ref(false);
        const showCalendar = ref(false);
        const infoTitle = ref('');
        const infoContent = ref('');

        // Meals
        const currentMealType = ref('');
        const currentCategory = ref('全部');
        const currentDish = ref(null);

        // Health recipes
        const healthRecipeType = ref('porridge');
        const healthRecipes = ref([]);
        const currentHealthRecipe = ref(null);

        // Exercise
        const exercisePlans = ref(EXERCISE_PLANS);
        const sportList = ref(SPORTS);
        const activeContext = ref(null);
        const timerSeconds = ref(0);
        const timerRunning = ref(false);
        let timerInterval = null;
        const currentExercisePlan = ref(null);
        const exerciseRecords = ref([]);

        // Cart
        const cartItems = ref([]);

        // Pay
        const payPassword = ref('');

        // Calendar
        const calendarYear = ref(new Date().getFullYear());
        const calendarMonth = ref(new Date().getMonth() + 1);
        const checkedDates = ref([]);

        // Chat
        const chatMessages = ref([]);
        const chatInput = ref('');

        // Profile edit
        const editHeight = ref('');
        const editWeight = ref('');
        const editAge = ref('');
        const editGender = ref('男');
        const selectedDiseases = ref([]);
        const profileData = ref(null);

        // Settings
        const settingsUsername = ref('');

        // Orders
        const orders = ref([]);

        // Nutrition
        const nutritionData = ref({ total_calories: 0, total_protein: 0, total_carbs: 0, exercise_calories: 0, water_cups: 0, water_target: 8 });

        // ==================== Computed ====================
        const totalMealCalories = computed(() => {
            let cal = 0;
            ['breakfast','lunch','dinner'].forEach(t => { if (dailyMeals[t]) cal += dailyMeals[t].calories; });
            return cal;
        });
        const cartTotal = computed(() => cartItems.value.reduce((s, i) => s + i.price, 0));
        const waterProgress = computed(() => Math.min(100, (waterCount.value / 8) * 100));
        const waterDisplay = computed(() => `${waterCount.value}/8 杯 (${waterCount.value * 200}ml)`);
        const daysInMonth = computed(() => new Date(calendarYear.value, calendarMonth.value, 0).getDate());
        const firstDayOfMonth = computed(() => new Date(calendarYear.value, calendarMonth.value - 1, 1).getDay());

        // ==================== Page switching ====================
        function switchToPage(pageId) {
            currentPage.value = pageId;
            if (pageId === 'healthRecipeListPage') loadHealthRecipes();
            if (pageId === 'ordersPage') loadOrders();
            if (pageId === 'profileEditPage') loadProfileForEdit();
            if (pageId === 'planPage') { nextTick(() => scrollChatBottom()); }
            if (pageId === 'nutritionPage') { nextTick(() => renderNutritionChart()); }
            if (pageId === 'sportPage') initSportModule();
        }

        // ==================== API helper ====================
        async function api(url, options = {}) {
            const res = await fetch(url, { credentials: 'same-origin', ...options });
            return res.json();
        }

        // ==================== Auth ====================
        async function doLogin() {
            if (!authUsername.value || !authPassword.value) return alert('请输入用户名和密码');
            const d = await api('/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: authUsername.value, password: authPassword.value }) });
            if (d.error) return alert(d.error);
            currentUser.value = { id: d.user_id, username: authUsername.value };
            showAuth.value = false;
            loadUserData();
        }
        async function doRegister() {
            if (!authUsername.value || !authPassword.value) return alert('请输入用户名和密码');
            const d = await api('/register', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: authUsername.value, password: authPassword.value }) });
            if (d.error) return alert(d.error);
            alert('注册成功，请登录');
            authMode.value = 'login';
        }
        function toggleAuthMode() { authMode.value = authMode.value === 'login' ? 'register' : 'login'; }
        async function logout() {
            await api('/logout', { method: 'POST' });
            currentUser.value = null;
            Object.keys(dailyMeals).forEach(k => dailyMeals[k] = null);
            waterCount.value = 0;
            chatMessages.value = [];
            showAuth.value = true;
            currentPage.value = 'homePage';
        }

        // ==================== User data ====================
        async function loadUserData() {
            try {
                const d = await api('/user_info');
                currentUser.value = { id: d.user_id || currentUser.value?.id, username: d.username, avatar: d.avatar, points: d.points };
                profileData.value = d;
                settingsUsername.value = d.username;
                if (d.medical_history) selectedDiseases.value = d.medical_history;
                const meals = await api('/get_daily_meals');
                Object.keys(dailyMeals).forEach(k => dailyMeals[k] = null);
                if (meals.meals) meals.meals.forEach(m => { dailyMeals[m.meal_type] = { name: m.food_name, calories: m.calories, price: m.price, protein: m.protein, carbs: m.carbs }; });
                const foods = await api('/foods');
                Object.assign(foodsData, foods);
                const w = await api('/get_water_count');
                waterCount.value = w.count || 0;
                const n = await api('/get_daily_nutrition');
                Object.assign(nutritionData.value, n);
            } catch (e) { console.error(e); }
        }

        // ==================== Water ====================
        function updateWaterCooldown(now) {
            if (!waterLastClick.value) { waterCooldown.value = 0; return; }
            const elapsed = Math.floor((now - waterLastClick.value) / 1000);
            const remaining = 3600 - elapsed;
            waterCooldown.value = Math.max(0, remaining);
        }
        async function waterCheckin() {
            if (waterCooldown.value > 0) return alert('请等待冷却时间结束');
            if (waterCount.value >= 8) return alert('今日饮水已满');
            const d = await api('/checkin', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type: 'water', detail: '饮水1杯' }) });
            if (d.success) { waterCount.value++; waterLastClick.value = Date.now(); waterCooldown.value = 3600; alert(`+${d.points_added}积分`); loadUserData(); }
            else alert(d.error);
        }
        // Water cooldown timer
        onMounted(() => {
            countdownInterval = setInterval(() => {
                if (waterLastClick.value) {
                    const elapsed = Math.floor((Date.now() - waterLastClick.value) / 1000);
                    waterCooldown.value = Math.max(0, 3600 - elapsed);
                }
            }, 1000);
        });

        // ==================== Meals / Dish selection ====================
        const filteredFoods = computed(() => {
            const list = foodsData[currentMealType.value] || [];
            if (currentCategory.value === '全部') return list;
            return list.filter(f => f.category === currentCategory.value);
        });

        function openDishCategory(type) {
            currentMealType.value = type;
            currentCategory.value = '全部';
            currentPage.value = 'dishListPage';
        }
        function selectCategory(cat) { currentCategory.value = cat; }
        function viewDishDetail(dish) { currentDish.value = dish; currentPage.value = 'dishDetailPage'; }
        function backToDishList() { currentPage.value = 'dishListPage'; }
        function addToCartFromDetail() {
            if (!currentDish.value) return;
            const existing = cartItems.value.find(i => i.name === currentDish.value.name);
            if (existing) existing.qty = (existing.qty || 1) + 1;
            else cartItems.value.push({ ...currentDish.value, qty: 1 });
            alert('已加入购物车');
        }
        async function selectDish(dish) {
            dailyMeals[currentMealType.value] = { name: dish.name, calories: dish.calories, price: dish.price, protein: dish.protein || 0, carbs: dish.carbs || 0 };
            await api('/save_meal', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ meal_type: currentMealType.value, food_name: dish.name, calories: dish.calories, price: dish.price, protein: dish.protein || 0, carbs: dish.carbs || 0 }) });
            currentPage.value = 'homePage';
            loadUserData();
        }
        function generateCart() {
            cartItems.value = [];
            Object.entries(dailyMeals).forEach(([type, meal]) => {
                if (meal) cartItems.value.push({ name: meal.name, price: meal.price, qty: 1, type });
            });
            showCart.value = true;
        }
        function removeCartItem(idx) { cartItems.value.splice(idx, 1); }
        function payOrder() { showCart.value = false; showPay.value = true; }
        async function confirmPay() {
            const pwd = payPassword.value;
            if (pwd.length !== 6 || !/^\d{6}$/.test(pwd)) return alert('请输入六位数字密码');
            alert('支付成功！(模拟)');
            showPay.value = false;
            payPassword.value = '';
            // Auto checkin for meals in cart
            const types = new Set(cartItems.value.map(i => i.type));
            for (const t of types) {
                if (['breakfast','lunch','dinner'].includes(t)) {
                    const d = await api('/checkin', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type: t, detail: `${t}打卡` }) });
                    if (d.success) alert(`${t}打卡成功！+${d.points_added}积分`);
                }
            }
            loadUserData();
        }

        // ==================== AI Chat ====================
        async function loadChatHistory() {
            const d = await api('/load_chat_history');
            chatMessages.value = (d.history || []).map(h => ({ role: h.role, content: h.content }));
            nextTick(() => scrollChatBottom());
        }
        async function sendChat() {
            const msg = chatInput.value.trim();
            if (!msg) return;
            chatMessages.value.push({ role: 'user', content: msg });
            chatInput.value = '';
            nextTick(() => scrollChatBottom());
            try {
                const d = await api('/ai_chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: msg }) });
                chatMessages.value.push({ role: 'assistant', content: d.reply || 'AI暂时无响应' });
                nextTick(() => scrollChatBottom());
            } catch (e) {
                chatMessages.value.push({ role: 'assistant', content: '网络错误' });
            }
        }
        async function clearChat() {
            if (!confirm('确定清空对话历史？')) return;
            await api('/clear_chat', { method: 'POST' });
            chatMessages.value = [];
        }
        function scrollChatBottom() {
            const box = document.getElementById('chatBoxPlan');
            if (box) box.scrollTop = box.scrollHeight;
        }
        // Tongue camera
        function openTongue() { showTongue.value = true; nextTick(() => startTongueCamera()); }
        function closeTongue() {
            const video = document.getElementById('tongueVideo');
            if (video && video.srcObject) { video.srcObject.getTracks().forEach(t => t.stop()); }
            showTongue.value = false;
        }
        function startTongueCamera() {
            const video = document.getElementById('tongueVideo');
            if (!video) return;
            navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } })
                .then(stream => { video.srcObject = stream; video.play(); })
                .catch(() => alert('无法访问摄像头'));
        }
        function captureTongue() {
            const video = document.getElementById('tongueVideo');
            const canvas = document.getElementById('tongueCanvas');
            if (!video || !canvas) return;
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            alert('拍照成功（舌诊分析功能暂未开放）');
        }

        // ==================== Health Recipes ====================
        async function loadHealthRecipes() {
            const d = await api('/health_recipes');
            healthRecipes.value = d[healthRecipeType.value] || [];
        }
        function setHealthRecipeType(type) { healthRecipeType.value = type; }
        function showHealthRecipeDetail(recipe) { currentHealthRecipe.value = recipe; currentPage.value = 'healthRecipeDetailPage'; }
        async function selectHealthRecipe(recipe) {
            const typeMap = { porridge: 'health_porridge', tea: 'health_tea', soup: 'health_soup', dish: 'health_dish' };
            const key = typeMap[healthRecipeType.value];
            dailyMeals[key] = { name: recipe.name, calories: recipe.calories, price: recipe.price, protein: 0, carbs: 0 };
            await api('/save_meal', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ meal_type: key, food_name: recipe.name, calories: recipe.calories, price: recipe.price }) });
            currentPage.value = 'homePage';
            loadUserData();
        }
        function getHealthRecipeImg(name, type) {
            const safe = name.replace(/[^a-zA-Z0-9\u4e00-\u9fff]/g, '_');
            return `/static/images/${safe}.jpg`;
        }

        // ==================== Exercise (Sport) ====================
        function initSportModule() { /* sport data loaded */ }
        function showExerciseDetail(plan) { currentExercisePlan.value = plan; currentPage.value = 'exerciseDetailPage'; }
        async function showExerciseRecords() {
            const d = await api('/get_exercise_records');
            exerciseRecords.value = d.records || [];
            showExerciseRecord.value = true;
        }
        function startSportTimer(sport) { activeContext.value = { ...sport, startTime: Date.now(), paused: false, elapsed: 0 }; timerSeconds.value = 0; timerRunning.value = true; startTimerTick(); }
        function startTimerTick() {
            if (timerInterval) clearInterval(timerInterval);
            timerInterval = setInterval(() => {
                if (!activeContext.value?.paused) {
                    timerSeconds.value++;
                    if (activeContext.value) activeContext.value.elapsed = timerSeconds.value;
                }
            }, 1000);
        }
        function pauseSportTimer() { if (activeContext.value) activeContext.value.paused = !activeContext.value.paused; }
        function resetSportTimer() { if (timerInterval) clearInterval(timerInterval); activeContext.value = null; timerSeconds.value = 0; timerRunning.value = false; }
        async function abortExercise() {
            const ctx = activeContext.value;
            if (ctx && ctx.elapsed > 0) {
                const cal = (ctx.elapsed / 60) * ctx.ratePerMin;
                await api('/save_exercise', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type: ctx.id, name: ctx.name, duration_seconds: ctx.elapsed, calories: cal.toFixed(1), award_points: ctx.elapsed >= 1800 }) });
            }
            resetSportTimer();
            loadUserData();
        }
        function formatTime(sec) { const m = Math.floor(sec / 60); const s = sec % 60; return `${m.toString().padStart(2,'0')}:${s.toString().padStart(2,'0')}`; }
        function joinPlan() {
            if (activeContext.value) {
                alert(`已将${activeContext.value.name}加入运动计划`);
            }
        }

        // ==================== Calendar ====================
        async function renderCalendar() {
            const d = await api(`/calendar_data?year=${calendarYear.value}&month=${calendarMonth.value}`);
            checkedDates.value = d.checked_dates || [];
        }
        function changeMonth(delta) {
            calendarMonth.value += delta;
            if (calendarMonth.value > 12) { calendarMonth.value = 1; calendarYear.value++; }
            else if (calendarMonth.value < 1) { calendarMonth.value = 12; calendarYear.value--; }
            renderCalendar();
        }
        async function toggleCalendarDay(dateStr) {
            await api('/toggle_calendar', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ date: dateStr }) });
            renderCalendar();
        }
        function todayStr() {
            const t = new Date();
            return `${t.getFullYear()}-${(t.getMonth()+1).toString().padStart(2,'0')}-${t.getDate().toString().padStart(2,'0')}`;
        }
        function calendarDays() {
            const days = [];
            const firstDay = firstDayOfMonth.value;
            const total = daysInMonth.value;
            for (let i = 0; i < firstDay; i++) days.push({ day: '', other: true });
            for (let d = 1; d <= total; d++) {
                const ds = `${calendarYear.value}-${calendarMonth.value.toString().padStart(2,'0')}-${d.toString().padStart(2,'0')}`;
                days.push({ day: d, dateStr: ds, isToday: ds === todayStr(), checked: checkedDates.value.includes(ds) });
            }
            return days;
        }

        // ==================== Points / Exchange / Orders ====================
        async function exchange(item) {
            if (!confirm(`确认兑换${item}？`)) return;
            const d = await api('/exchange', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ item }) });
            if (d.error) alert(d.error);
            else { alert('兑换成功'); loadUserData(); }
        }
        async function loadOrders() {
            const d = await api('/get_orders');
            orders.value = d.orders || [];
        }

        // ==================== Profile ====================
        async function loadProfileForEdit() {
            const d = profileData.value?.profile || {};
            editHeight.value = d.height || '';
            editWeight.value = d.weight || '';
            editAge.value = d.age || '';
            editGender.value = d.gender || '男';
        }
        async function saveProfile() {
            await api('/save_profile', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ height: editHeight.value, weight: editWeight.value, age: editAge.value, gender: editGender.value, diseases: selectedDiseases.value }) });
            alert('保存成功');
            currentPage.value = 'profilePage';
            loadUserData();
        }
        function toggleDisease(disease) {
            const idx = selectedDiseases.value.findIndex(i => i.disease === disease);
            if (idx >= 0) selectedDiseases.value.splice(idx, 1);
            else { const detail = prompt(`请输入${disease}详情（如过敏原、严重程度），无则留空`); selectedDiseases.value.push({ disease, detail: detail || '' }); }
        }
        async function uploadAvatar(e) {
            const file = e.target.files[0];
            if (!file) return;
            const form = new FormData();
            form.append('avatar', file);
            await api('/upload_avatar', { method: 'POST', body: form });
            loadUserData();
        }
        async function changeUsername() {
            const name = prompt('输入新用户名');
            if (!name) return;
            const d = await api('/change_username', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ new_username: name }) });
            if (d.error) alert(d.error);
            else { alert('用户名修改成功'); loadUserData(); }
        }
        async function changePassword() {
            const oldPw = prompt('输入旧密码'); if (!oldPw) return;
            const newPw = prompt('输入新密码'); if (!newPw) return;
            const d = await api('/change_password', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ old_password: oldPw, new_password: newPw }) });
            if (d.error) alert(d.error);
            else alert('密码修改成功，请重新登录');
        }

        // ==================== Info Modal ====================
        function openInfo(title) { infoTitle.value = title; infoContent.value = '暂无内容'; showInfo.value = true; }

        // ==================== Nutrition Chart (ECharts) ====================
        function renderNutritionChart() {
            nextTick(() => {
                const dom = document.getElementById('nutritionChart');
                if (!dom || !window.echarts) return;
                const chart = echarts.init(dom);
                chart.setOption({
                    tooltip: { trigger: 'item' },
                    series: [{
                        type: 'pie',
                        radius: ['50%', '75%'],
                        label: { show: true, formatter: '{b}\n{d}%' },
                        data: [
                            { value: nutritionData.value.total_protein * 4 || 0, name: '蛋白质', itemStyle: { color: '#C75C3A' } },
                            { value: nutritionData.value.total_carbs * 4 || 0, name: '碳水', itemStyle: { color: '#D4AF37' } },
                            { value: Math.max(0, nutritionData.value.total_calories - (nutritionData.value.total_protein * 4) - (nutritionData.value.total_carbs * 4)), name: '脂肪', itemStyle: { color: '#8B6F4E' } }
                        ].filter(d => d.value > 0)
                    }]
                });
            });
        }

        // ==================== Plan tag selection ====================
        async function applyPlan(tag) {
            await api('/save_profile', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ plan_tag: tag }) });
            alert(`已应用"${tag}"方案`);
            loadUserData();
            chatMessages.value.push({ role: 'assistant', content: `方案已更新为"${tag}"，有什么可以帮您？` });
        }

        // ==================== Lifecycle ====================
        onMounted(() => {
            // Try to restore session
            api('/user_info').then(d => {
                if (d.username) {
                    currentUser.value = { username: d.username, points: d.points, avatar: d.avatar };
                    showAuth.value = false;
                    loadUserData();
                }
            }).catch(() => {});
        });

        // ==================== Data constants (from old app.js) ====================
        return {
            // State
            currentUser, currentPage, dailyMeals, foodsData, waterCount, waterCooldown,
            authMode, authUsername, authPassword,
            showAuth, showNotify, showCart, showPay, openInfo, showExerciseRecord, showTongue, showCalendar,
            infoTitle, infoContent,
            currentMealType, currentCategory, currentDish,
            healthRecipeType, healthRecipes, currentHealthRecipe,
            exercisePlans, sportList, activeContext, timerSeconds, timerRunning, currentExercisePlan, exerciseRecords,
            cartItems, payPassword,
            calendarYear, calendarMonth, checkedDates,
            chatMessages, chatInput,
            editHeight, editWeight, editAge, editGender, selectedDiseases, profileData,
            settingsUsername, orders, nutritionData,
            // Computed
            totalMealCalories, cartTotal, waterProgress, waterDisplay, daysInMonth, firstDayOfMonth,
            filteredFoods,
            // Methods
            switchToPage, doLogin, doRegister, toggleAuthMode, logout,
            loadUserData, loadChatHistory,
            waterCheckin,
            openDishCategory, selectCategory, viewDishDetail, backToDishList,
            addToCartFromDetail, selectDish, generateCart, removeCartItem, payOrder, confirmPay,
            sendChat, clearChat, openTongue, closeTongue, captureTongue,
            loadHealthRecipes, setHealthRecipeType, showHealthRecipeDetail, selectHealthRecipe, getHealthRecipeImg,
            showExerciseDetail, showExerciseRecords, startSportTimer, pauseSportTimer, resetSportTimer, abortExercise,
            formatTime, joinPlan,
            renderCalendar, changeMonth, toggleCalendarDay, todayStr, calendarDays,
            exchange, loadOrders,
            loadProfileForEdit, saveProfile, toggleDisease, uploadAvatar, changeUsername, changePassword,
            openInfo,
            ALL_DISEASES, DISEASE_TAG_CLASS
        };
    }
});

app.mount('#app');
