import difflib
import json
import os
import random
import re
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN Secret topilmadi.")

API_URL = f"https://api.telegram.org/bot{TOKEN}/"
NORMAL_QUESTION_SECONDS = 15
PRO_QUESTION_SECONDS = 25
NORMAL_EXP = 8
PRO_EXP = 15
PARTIAL_EXP_DIVISOR = 2
STREAK_SIZE = 10
STREAK_BONUS_EXP = 20
POLL_SECONDS = 2

START_BUTTON = "▶️ Boshlash"
PRO_BUTTON = "🔥 PRO rejim"
SHADOWING_BUTTON = "🎧 Shadowing"
NEXT_BUTTON = "➡️ Keyingi savol"
RANKING_BUTTON = "🏆 Reyting"
RESULT_BUTTON = "📊 Natijam"
STOP_BUTTON = "⏹ To‘xtatish"


@dataclass(frozen=True)
class Question:
    uzbek: str
    english: str


@dataclass
class Player:
    name: str
    exp: int = 0
    answered: int = 0
    correct: int = 0
    streak: int = 0


@dataclass
class ActiveQuestion:
    chat_id: int
    question: Question
    deadline: float
    pro: bool
    reward: int


QUESTIONS = [
    Question("Men odatda ertalab juda erta uyg‘onaman.", "I usually wake up early in the morning."),
    Question("Bo‘sh vaqtimda musiqa tinglashni yoqtiraman.", "I like listening to music in my free time."),
    Question("Men ko‘pincha do‘stlarim bilan vaqt o‘tkazaman.", "I often spend time with my friends."),
    Question("Mening sevimli taomim — pitsa.", "My favorite food is pizza."),
    Question("Men gavjum joylarni unchalik yoqtirmayman.", "I don't really like crowded places."),
    Question("Men odatda maktabga taksida boraman.", "I usually go to school by taxi."),
    Question("Uyda film tomosha qilishni yoqtiraman.", "I enjoy watching movies at home."),
    Question("Ba’zan do‘stlarim bilan o‘yin o‘ynayman.", "I sometimes play games with my friends."),
    Question("Men yoz faslini yaxshi ko‘raman, chunki havo iliq bo‘ladi.", "I like summer because the weather is warm."),
    Question("Mening sevimli fanim — ingliz tili.", "My favorite subject is English."),
    Question("Menimcha, ingliz tili juda foydali.", "I think English is very useful."),
    Question("Men odatda ertalab choy ichaman.", "I usually have tea in the morning."),
    Question("Men ko‘pincha uxlashdan oldin telefonimdan foydalanaman.", "I often use my phone before going to bed."),
    Question("Kechqurun sayr qilishni yoqtiraman.", "I like going for a walk in the evening."),
    Question("Men televizorni tez-tez ko‘rmayman.", "I don't watch TV very often."),
    Question("Men tinch joyda o‘qishni afzal ko‘raman.", "I prefer studying in a quiet place."),
    Question("Mening bir nechta yaqin do‘stlarim bor.", "I have a few close friends."),
    Question("Yangi narsalarni o‘rganishni yoqtiraman.", "I enjoy learning new things."),
    Question("Odatda dam olish kunlarimni uyda o‘tkazaman.", "I usually spend my weekends at home."),
    Question("Men ingliz tilimni yaxshilamoqchiman.", "I want to improve my English."),
    Question("Men kunimni odatda bir piyola choy bilan boshlayman.", "I usually start my day with a cup of tea."),
    Question("Men telefonda ancha ko‘p vaqt o‘tkazaman.", "I spend quite a lot of time on my phone."),
    Question("Ob-havo yomon bo‘lsa, uyda qolishni afzal ko‘raman.", "I prefer staying at home when the weather is bad."),
    Question("Do‘stlarim bilan vaqt o‘tkazishni juda yoqtiraman.", "I really enjoy hanging out with my friends."),
    Question("Biror ish qilayotganimda odatda musiqa tinglayman.", "I usually listen to music when I'm doing something."),
    Question("Menimcha, ingliz tili kelajagim uchun muhim.", "I think English is important for my future."),
    Question("Hafta davomida bo‘sh vaqtim ko‘p emas.", "I don't have much free time during the week."),
    Question("Odatda kechqurun o‘qiyman, chunki o‘sha payt tinchroq bo‘ladi.", "I normally study in the evening because it's quieter."),
    Question("Bo‘sh vaqtim bo‘lsa, ayniqsa film tomosha qilishni yoqtiraman.", "I enjoy watching films, especially when I have some free time."),
    Question("Men texnologiyaga juda qiziqaman, deb ayta olaman.", "I would say that I'm quite interested in technology."),
    Question("Yolg‘iz sayohat qilishdan ko‘ra do‘stlarim bilan sayohat qilishni afzal ko‘raman.", "I prefer travelling with my friends rather than alone."),
    Question("Men odatda uyda o‘zimni xotirjamroq his qilaman.", "I usually feel more relaxed at home."),
    Question("Hozirda gapirish ko‘nikmalarimni yaxshilashga harakat qilyapman.", "I'm trying to improve my speaking skills these days."),
    Question("Men erta turishni unchalik yoqtirmayman.", "I don't really enjoy getting up early."),
    Question("Do‘stlarim bilan aloqada bo‘lish uchun ko‘pincha ijtimoiy tarmoqlardan foydalanaman.", "I often use social media to keep in touch with my friends."),
    Question("Menimcha, dam olish kunlari hordiq chiqarish uchun yaxshi imkoniyat.", "I think weekends are a good chance to relax."),
    Question("Ba’zan shunchaki toza havo olish uchun tashqariga chiqaman.", "I sometimes go out just to get some fresh air."),
    Question("Sayr qilayotganda musiqa tinglashni juda yoqtiraman.", "I'm quite fond of listening to music while walking."),
    Question("Odatda dam olish kunlari uchun rejalarimni oldindan tuzaman.", "I usually make plans for the weekend in advance."),
    Question("Menimcha, ingliz tilini o‘rganish ko‘plab imkoniyatlarni ochishi mumkin.", "I think learning English can open up many opportunities."),
    Question("Men yangi narsalarni o‘rganishga juda qiziqaman, deb ayta olaman.", "I’d say that I’m quite interested in learning new things."),
    Question("Menga eng yoqadigan mashg‘ulotlardan biri — do‘stlarim bilan vaqt o‘tkazish.", "One thing I really enjoy doing is spending time with my friends."),
    Question("Dam olishim kerak bo‘lganda musiqa tinglashga moyilman.", "I tend to listen to music whenever I need to relax."),
    Question("Bo‘sh vaqtimda film tomosha qilishni juda yoqtiraman.", "I’m quite fond of watching movies in my spare time."),
    Question("Odatda biror joy gavjum bo‘lishidan ko‘ra uyda qolishni afzal ko‘raman.", "I usually prefer staying at home rather than going somewhere crowded."),
    Question("Menimcha, ingliz tili kundalik hayotimning muhim qismiga aylandi.", "I think learning English has become an important part of my daily life."),
    Question("Shu kunlarda gapirganda o‘zimga bo‘lgan ishonchimni oshirishga harakat qilyapman.", "These days, I’m trying to become more confident when I speak English."),
    Question("Atrofda shovqin ko‘p bo‘lmasa, yaxshiroq o‘qishga moyilman.", "I tend to study better when there isn’t much noise around me."),
    Question("Menimcha, texnologiya kundalik hayotimda katta rol o‘ynaydi.", "I’d say that technology plays a big role in my everyday life."),
    Question("Men odatda do‘stlarim bilan muloqot qilish va foydali ma’lumot topish uchun telefonimdan foydalanaman.", "I usually use my phone to communicate with friends and find useful information."),
    Question("Bo‘sh vaqtim bo‘lsa, odatda sayr qilaman yoki musiqa tinglayman.", "When I have some free time, I normally go for a walk or listen to music."),
    Question("Men gavjum joylarga unchalik qiziqmayman, chunki ular menga biroz stressli tuyuladi.", "I’m not really into crowded places because I find them a bit stressful."),
    Question("Dam olish kunlarimni shunchaki yotoqda yotishdan ko‘ra foydali ish bilan o‘tkazishni afzal ko‘raman.", "I prefer spending my weekends doing something useful rather than just staying in bed."),
    Question("Menimcha, sayohat qilish turli madaniyatlarni boshdan kechirishning ajoyib usuli.", "I think travelling is a great way to experience different cultures."),
    Question("Men muloqot ko‘nikmalarimni yaxshilashga doimo qiziqib kelganman.", "I’ve always been interested in improving my communication skills."),
    Question("Mening tug‘ilib o‘sgan joyimda yoqadigan narsalardan biri — u nisbatan tinch.", "One of the things I like about my hometown is that it’s relatively peaceful."),
    Question("Ertalab o‘zimni unumliroq his qilishga moyilman.", "I tend to feel more productive in the morning."),
    Question("Menimcha, o‘qish va dam olish o‘rtasida yaxshi muvozanat bo‘lishi muhim.", "I think having a good balance between studying and relaxing is important."),
    Question("Charchaganimda odatda qisqa tanaffus qilaman va o‘zimga yoqadigan ish bilan shug‘ullanaman.", "Whenever I feel tired, I usually take a short break and do something I enjoy."),
    Question("Kelajakda ravonroq gapirishni va ingliz tilida tabiiyroq so‘zlashni xohlayman.", "In the future, I’d like to become more fluent and speak English more naturally."),
]

PRO_QUESTIONS = [
    Question(
        "Garchi texnologiya kundalik hayotimizni ancha qulaylashtirgan bo‘lsa-da, undan oqilona foydalanish muhim.",
        "Although technology has made our daily lives much more convenient, it is important to use it wisely.",
    ),
    Question(
        "Menimcha, chet tilini muntazam mashq qilish, hatto kuniga atigi yigirma daqiqa bo‘lsa ham, katta natija beradi.",
        "I believe that practising a foreign language regularly can make a big difference, even if it is only for twenty minutes a day.",
    ),
    Question(
        "Agar kelajakda chet elda o‘qish imkoniyatiga ega bo‘lsam, bu imkoniyatdan albatta foydalanardim.",
        "If I had the opportunity to study abroad in the future, I would definitely take it.",
    ),
    Question(
        "Muvaffaqiyatga erishish nafaqat iste’dodga, balki qiyinchiliklarga qaramay harakat qilishga ham bog‘liq.",
        "Achieving success depends not only on talent but also on continuing to work hard despite difficulties.",
    ),
    Question(
        "Ijtimoiy tarmoqlar odamlarni bog‘lab turishi mumkin, ammo ulardan ortiqcha foydalanish vaqtni behuda sarflashga olib keladi.",
        "Social media can help people stay connected, but using it excessively can lead to wasting time.",
    ),
    Question(
        "O‘tgan yili o‘rgangan eng foydali narsalarimdan biri vaqtimni samaraliroq rejalashtirish bo‘ldi.",
        "One of the most useful things I learned last year was how to manage my time more effectively.",
    ),
    Question(
        "Menimcha, odamlar xatolaridan qo‘rqmasliklari kerak, chunki xatolar rivojlanish uchun muhim imkoniyat bo‘lishi mumkin.",
        "I think people should not be afraid of making mistakes because mistakes can be an important opportunity for growth.",
    ),
    Question(
        "Agar odamlar jamoat transportidan ko‘proq foydalansalar, shaharlardagi tirbandlik va havo ifloslanishi kamayishi mumkin.",
        "If more people used public transport, traffic congestion and air pollution in cities could be reduced.",
    ),
    Question(
        "Bo‘sh vaqtimda yangi ko‘nikmalarni o‘rganishga harakat qilaman, chunki bu menga o‘zimga bo‘lgan ishonchni oshirishga yordam beradi.",
        "In my free time, I try to learn new skills because this helps me become more confident.",
    ),
    Question(
        "Kelajakda qanday kasb tanlashimdan qat’i nazar, ingliz tilini yaxshi bilish menga ko‘plab eshiklarni ochishiga ishonaman.",
        "Whatever career I choose in the future, I believe that knowing English well will open many doors for me.",
    ),
    Question(
        "Uzoq muddatli maqsadga erishish uchun inson vaqtinchalik qiyinchiliklarga sabr va qat’iyat bilan bardosh berishi kerak.",
        "To achieve a long-term goal, a person must endure temporary difficulties with patience and perseverance.",
    ),
    Question(
        "Ishlarni to‘g‘ri ustuvorlashtirish muhim, aks holda eng zarur vazifalar e’tibordan chetda qolishi mumkin.",
        "It is important to prioritise tasks properly; otherwise, the most essential responsibilities may be overlooked.",
    ),
    Question(
        "Atrof-muhitga zararli ta’sirni kamaytirish uchun kompaniyalar barqaror ishlab chiqarish usullariga o‘tishlari kerak.",
        "Companies should adopt sustainable production methods in order to mitigate their harmful impact on the environment.",
    ),
    Question(
        "Qaror qabul qilishdan oldin muammoning qisqa muddatli va uzoq muddatli oqibatlarini hisobga olish kerak.",
        "Before making a decision, we should take the short-term and long-term consequences of the problem into account.",
    ),
    Question(
        "O‘z xatti-harakatlari uchun javobgarlikni o‘z zimmasiga olish insonning yetukligini ko‘rsatadi.",
        "Taking accountability for one's actions is a sign of a person's maturity.",
    ),
    Question(
        "Murakkab vaziyatlarda xotirjamlikni saqlash va muammoga boshqa nuqtayi nazardan qarash foydali bo‘lishi mumkin.",
        "In complicated situations, staying calm and looking at the problem from a different perspective can be beneficial.",
    ),
    Question(
        "Aniq ma’lumot bo‘lmasa, vaziyatning mumkin bo‘lgan oqibatlari haqida shoshilinch xulosa chiqarmaslik kerak.",
        "Without clear information, we should avoid making hasty conclusions about the possible implications of the situation.",
    ),
    Question(
        "Muntazam o‘qish yangi bilimlarni mustahkamlashga yordam beradi va unutib qo‘yish ehtimolini kamaytiradi.",
        "Regular study helps reinforce new knowledge and reduces the likelihood of forgetting it.",
    ),
    Question(
        "Garchi bu usul dastlab ko‘proq vaqt talab qilsa-da, uzoq muddatda u ancha samarali bo‘lishi mumkin.",
        "Although this method may require more time initially, it can be considerably more effective in the long run.",
    ),
    Question(
        "Odamlar turli fikrlarga ega bo‘lishi tabiiy, ammo hurmat bilan muloqot qilish kelishmovchiliklarni kamaytiradi.",
        "It is natural for people to have different opinions, but respectful communication can reduce disagreements.",
    ),
    Question(
        "Yetarli uyqu va sog‘lom ovqatlanish aqliy faoliyatga ijobiy ta’sir ko‘rsatib, diqqatni jamlashni osonlashtiradi.",
        "Adequate sleep and a healthy diet have a positive effect on mental performance and make it easier to concentrate.",
    ),
]

SHADOWING_VIDEOS = [
    ("BBC 6 Minute English — shadowing playlist", "https://www.youtube.com/playlist?list=PLDvz1wX9h_ZauwGAHBkOzG5OY87LKyrZ6"),
    ("Slow English Shadowing Practice", "https://www.youtube.com/watch?v=AeO4C6Ud3iY"),
    ("BBC Learning English — 10 minute playlist", "https://www.youtube.com/playlist?list=PLjeg_-PmDILgHLsSz084aFYq7r5x7VN3e"),
    ("English Shadowing Practice playlist", "https://www.youtube.com/playlist?list=PLPtDqo0mKJodJk12Hy-k_m2Xv9p9oWHsD"),
    ("Shadowing English Practice playlist", "https://www.youtube.com/playlist?list=PLLHMv5igcGMRci4RbiWXW85oOktZsQ00J"),
    ("Slow English Listening Practice", "https://www.youtube.com/watch?v=9_8HRWRRClk"),
    ("A2–B1 English Shadowing Practice", "https://www.youtube.com/playlist?list=PLP1Pag3gzpH7inOqZrTcHIVcZ2R-73Szz"),
    ("Intermediate Shadowing Speaking Practice", "https://www.youtube.com/watch?v=H6Y6lJ4mahg"),
    ("Shadowing Practice for Intermediate Learners", "https://www.youtube.com/watch?v=Es3QtQpBrxU"),
    ("How to do shadowing properly", "https://www.youtube.com/watch?v=g-n4kQP9rMQ"),
]

players: dict[int, Player] = {}
active_questions: dict[int, ActiveQuestion] = {}
waiting_for_next: dict[int, tuple[int, bool]] = {}
question_decks: dict[tuple[int, bool], list[Question]] = {}


def telegram(method: str, payload: dict[str, Any] | None = None) -> Any:
    body = json.dumps(payload or {}).encode("utf-8")
    request = Request(
        API_URL + method,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=35) as response:
        result = json.loads(response.read().decode("utf-8"))
    if not result.get("ok"):
        raise RuntimeError(f"Telegram API xatosi: {result}")
    return result.get("result")


def keyboard(rows: list[list[str]]) -> dict[str, Any]:
    return {
        "keyboard": [[{"text": item} for item in row] for row in rows],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }


def send_message(chat_id: int, text: str, rows: list[list[str]] | None = None) -> None:
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    if rows is not None:
        payload["reply_markup"] = keyboard(rows)
    telegram("sendMessage", payload)


def normalize_answer(text: str) -> str:
    text = text.casefold()
    text = text.replace("’", "'").replace("‘", "'").replace("`", "'")
    text = text.replace("'", "")
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def explain_mistake(user_answer: str, correct_answer: str) -> str:
    user_words = normalize_answer(user_answer).split()
    correct_words = normalize_answer(correct_answer).split()
    matcher = difflib.SequenceMatcher(None, user_words, correct_words)

    for tag, start_a, end_a, start_b, end_b in matcher.get_opcodes():
        if tag == "equal":
            continue
        written = " ".join(user_words[start_a:end_a]) or "hech narsa"
        expected = " ".join(correct_words[start_b:end_b]) or "hech narsa"
        if tag == "replace":
            return f"Xato qism: “{written}” o‘rniga “{expected}” bo‘lishi kerak."
        if tag == "delete":
            return f"Xato qism: “{written}” so‘zini yozmaslik kerak."
        return f"Xato qism: “{expected}” so‘zini qo‘shish kerak."
    return "So‘zlar to‘g‘ri, lekin gap tartibi yoki yozilishida xato bor."


def is_close_answer(user_answer: str, correct_answer: str) -> bool:
    user_normalized = normalize_answer(user_answer)
    correct_normalized = normalize_answer(correct_answer)
    if not user_normalized or user_normalized == correct_normalized:
        return False

    character_similarity = difflib.SequenceMatcher(
        None, user_normalized, correct_normalized
    ).ratio()
    word_similarity = difflib.SequenceMatcher(
        None, user_normalized.split(), correct_normalized.split()
    ).ratio()
    return character_similarity >= 0.72 and word_similarity >= 0.58


def shadowing_text() -> str:
    lines = [
        "🎧 Shadowing mashqlari",
        "",
        "Videoni tinglang, keyin gapiruvchidan keyin baland ovozda takrorlang.",
        "Avval sekinroq videolardan boshlang:",
        "",
    ]
    for number, (title, url) in enumerate(SHADOWING_VIDEOS, start=1):
        lines.append(f"{number}. {title}\n{url}\n")
    return "\n".join(lines)


def player_level(exp: int) -> int:
    return exp // 50 + 1


def player_badges(player: Player) -> str:
    badges: list[str] = []
    if player.correct >= 1:
        badges.append("Birinchi g‘alaba")
    if player.streak >= 5:
        badges.append("5 lik streak")
    if player.streak >= 10:
        badges.append("10 lik streak")
    if player.exp >= 100:
        badges.append("EXP yig‘uvchi")
    return ", ".join(badges) if badges else "Hali badge yo‘q"


def player_name(user: dict[str, Any]) -> str:
    parts = [user.get("first_name", "").strip(), user.get("last_name", "").strip()]
    return " ".join(part for part in parts if part) or user.get("username") or "Foydalanuvchi"


def get_player(user: dict[str, Any]) -> Player:
    user_id = int(user["id"])
    name = player_name(user)
    if user_id not in players:
        players[user_id] = Player(name=name)
    else:
        players[user_id].name = name
    return players[user_id]


def next_question(user_id: int, pro: bool = False) -> Question:
    deck_key = (user_id, pro)
    deck = question_decks.setdefault(deck_key, [])
    if not deck:
        deck.extend(PRO_QUESTIONS if pro else QUESTIONS)
        random.shuffle(deck)
    return deck.pop()


def send_question(chat_id: int, user_id: int, pro: bool = False) -> None:
    waiting_for_next.pop(user_id, None)
    question = next_question(user_id, pro)
    seconds = PRO_QUESTION_SECONDS if pro else NORMAL_QUESTION_SECONDS
    reward = PRO_EXP if pro else NORMAL_EXP
    active_questions[user_id] = ActiveQuestion(
        chat_id=chat_id,
        question=question,
        deadline=time.monotonic() + seconds,
        pro=pro,
        reward=reward,
    )
    mode = "🔥 PRO savol" if pro else "Oddiy savol"
    send_message(
        chat_id,
        f"{mode}\n"
        "O‘zbekcha gapni ingliz tiliga tarjima qiling:\n\n"
        f"{question.uzbek}\n\n"
        f"Javobingizni yozing. Sizda {seconds} soniya bor.\n"
        f"To‘g‘ri javob uchun {reward} EXP.",
        [[STOP_BUTTON]],
    )


def ranking_text(current_user_id: int | None = None) -> str:
    if not players:
        return "Hali reytingda hech kim yo‘q."

    ordered = sorted(
        players.items(),
        key=lambda item: (-item[1].exp, -item[1].correct, item[1].name.casefold()),
    )
    lines = ["🏆 EXP reytingi:"]
    for position, (_, player) in enumerate(ordered[:10], start=1):
        lines.append(
            f"{position}. {player.name} — Level {player_level(player.exp)}, "
            f"{player.exp} EXP "
            f"({player.correct}/{player.answered} to‘g‘ri)"
        )

    if current_user_id is not None:
        own_position = next(
            (position for position, (user_id, _) in enumerate(ordered, start=1)
             if user_id == current_user_id),
            None,
        )
        if own_position and own_position > 10:
            player = players[current_user_id]
            lines.append(f"\nSizning o‘rningiz: {own_position}. {player.exp} EXP")
    return "\n".join(lines)


def send_menu(chat_id: int, user: dict[str, Any]) -> None:
    player = get_player(user)
    send_message(
        chat_id,
        f"Salom, {player.name}!\n\n"
        f"Levelingiz: {player_level(player.exp)} | EXP: {player.exp}\n"
        f"Badge: {player_badges(player)}\n\n"
        "Men sizga o‘zbekcha gap beraman, siz uning inglizchasini yozasiz.\n"
        f"Oddiy rejim: {NORMAL_QUESTION_SECONDS} soniya, {NORMAL_EXP} EXP.\n"
        f"PRO rejim: {PRO_QUESTION_SECONDS} soniya, {PRO_EXP} EXP.\n"
        f"Har {STREAK_SIZE} ta ketma-ket to‘g‘ri javob uchun +{STREAK_BONUS_EXP} EXP bonus.\n\n"
        "Viktorinani boshlash uchun pastdagi tugmani bosing.",
        [[START_BUTTON, PRO_BUTTON], [SHADOWING_BUTTON], [RANKING_BUTTON, RESULT_BUTTON]],
    )


def send_result(chat_id: int, user_id: int, text: str, active: ActiveQuestion) -> None:
    waiting_for_next[user_id] = (chat_id, active.pro)
    send_message(
        chat_id,
        text,
        [[NEXT_BUTTON], [PRO_BUTTON], [SHADOWING_BUTTON], [RANKING_BUTTON, RESULT_BUTTON], [STOP_BUTTON]],
    )


def expire_question(user_id: int) -> None:
    active = active_questions.pop(user_id, None)
    if active is None:
        return
    player = players.get(user_id)
    if player:
        player.answered += 1
        player.streak = 0
    send_result(
        active.chat_id,
        user_id,
        "⏰ Vaqt tugadi.\n\n"
        f"To‘g‘ri javob: {active.question.english}\n\n"
        "Keyingi savol uchun tugmani bosing.",
        active,
    )


def answer_question(chat_id: int, user: dict[str, Any], text: str) -> None:
    user_id = int(user["id"])
    active = active_questions.get(user_id)
    if active is None:
        if user_id in waiting_for_next:
            send_message(chat_id, "Avval “Keyingi savol” tugmasini bosing.")
        else:
            send_message(chat_id, "Viktorinani boshlash uchun “Boshlash” tugmasini bosing.")
        return

    if time.monotonic() > active.deadline:
        expire_question(user_id)
        return

    active_questions.pop(user_id, None)
    player = get_player(user)
    player.answered += 1
    old_level = player_level(player.exp)

    exact = normalize_answer(text) == normalize_answer(active.question.english)
    close = not exact and is_close_answer(text, active.question.english)

    if exact:
        player.correct += 1
        player.streak += 1
        bonus = STREAK_BONUS_EXP if player.streak % STREAK_SIZE == 0 else 0
        earned = active.reward + bonus
        player.exp += earned
        bonus_text = (
            f"\n🎁 {STREAK_SIZE} ta ketma-ket to‘g‘ri javob uchun "
            f"+{STREAK_BONUS_EXP} EXP bonus!"
            if bonus
            else ""
        )
        result = (
            f"✅ To‘g‘ri! +{active.reward} EXP.\n"
            f"Ketma-ket to‘g‘ri javoblar: {player.streak}\n"
            f"Jami EXP: {player.exp}{bonus_text}\n\n"
            "Keyingi savol uchun tugmani bosing."
        )
    elif close:
        partial_exp = max(1, active.reward // PARTIAL_EXP_DIVISOR)
        player.exp += partial_exp
        player.streak = 0
        result = (
            f"🟡 Javobingiz yaqin! +{partial_exp} EXP.\n\n"
            f"Siz yozdingiz: {text}\n"
            f"To‘g‘ri javob: {active.question.english}\n"
            f"Kamchilik: {explain_mistake(text, active.question.english)}\n\n"
            "Keyingi savol uchun tugmani bosing."
        )
    else:
        player.streak = 0
        result = (
            "❌ Noto‘g‘ri.\n\n"
            f"Siz yozdingiz: {text}\n"
            f"To‘g‘ri javob: {active.question.english}\n"
            f"{explain_mistake(text, active.question.english)}\n\n"
            "Keyingi savol uchun tugmani bosing."
        )
    new_level = player_level(player.exp)
    if new_level > old_level:
        result += f"\n🎉 Tabriklaymiz! Siz Level {new_level} ga chiqdingiz!"
    send_result(chat_id, user_id, result, active)


def handle_command(chat_id: int, user: dict[str, Any], command: str) -> None:
    user_id = int(user["id"])
    player = get_player(user)

    if command == "/start":
        active_questions.pop(user_id, None)
        waiting_for_next.pop(user_id, None)
        send_menu(chat_id, user)
    elif command in {"/quiz", "/begin"}:
        send_question(chat_id, user_id)
    elif command == "/pro":
        send_question(chat_id, user_id, pro=True)
    elif command in {"/shadowing", "/shadow"}:
        send_message(
            chat_id,
            shadowing_text(),
            [[START_BUTTON, PRO_BUTTON], [RANKING_BUTTON, RESULT_BUTTON]],
        )
    elif command in {"/reyting", "/ranking", "/top"}:
        send_message(
            chat_id,
            ranking_text(user_id),
            [[START_BUTTON, PRO_BUTTON], [SHADOWING_BUTTON], [RANKING_BUTTON, RESULT_BUTTON]],
        )
    elif command in {"/natija", "/score"}:
        send_message(
            chat_id,
            f"📊 {player.name}, natijangiz:\n"
            f"Level: {player_level(player.exp)}\n"
            f"EXP: {player.exp}\n"
            f"To‘g‘ri javoblar: {player.correct}/{player.answered}\n"
            f"Ketma-ketlik: {player.streak}\n"
            f"Badge: {player_badges(player)}",
            [[START_BUTTON, PRO_BUTTON], [SHADOWING_BUTTON], [RANKING_BUTTON, RESULT_BUTTON]],
        )
    elif command in {"/stop", "/tugatish"}:
        active_questions.pop(user_id, None)
        waiting_for_next.pop(user_id, None)
        send_menu(chat_id, user)
    else:
        send_message(chat_id, "Noma’lum buyruq. /start yoki /quiz dan foydalaning.")


def handle_text(chat_id: int, user: dict[str, Any], text: str) -> None:
    user_id = int(user["id"])
    get_player(user)

    if text == START_BUTTON:
        send_question(chat_id, user_id)
    elif text == PRO_BUTTON:
        send_question(chat_id, user_id, pro=True)
    elif text == SHADOWING_BUTTON:
        send_message(chat_id, shadowing_text())
    elif text == NEXT_BUTTON:
        if user_id in waiting_for_next:
            next_chat_id, pro = waiting_for_next[user_id]
            send_question(next_chat_id, user_id, pro=pro)
        elif user_id in active_questions:
            send_message(chat_id, "Avval joriy savolga javob bering.")
        else:
            send_question(chat_id, user_id)
    elif text == RANKING_BUTTON:
        send_message(chat_id, ranking_text(user_id))
    elif text == RESULT_BUTTON:
        player = players[user_id]
        send_message(
            chat_id,
            f"📊 Natijangiz:\nLevel: {player_level(player.exp)}\n"
            f"EXP: {player.exp}\n"
            f"To‘g‘ri javoblar: {player.correct}/{player.answered}\n"
            f"Ketma-ketlik: {player.streak}\n"
            f"Badge: {player_badges(player)}",
        )
    elif text == STOP_BUTTON:
        active_questions.pop(user_id, None)
        waiting_for_next.pop(user_id, None)
        send_menu(chat_id, user)
    else:
        answer_question(chat_id, user, text)


def handle_update(update: dict[str, Any]) -> None:
    message = update.get("message")
    if not message or not message.get("from") or not message.get("chat"):
        return

    user = message["from"]
    chat_id = int(message["chat"]["id"])
    text = message.get("text", "").strip()
    if not text:
        return

    if text.startswith("/"):
        command = text.split(maxsplit=1)[0].split("@", maxsplit=1)[0].casefold()
        handle_command(chat_id, user, command)
    else:
        handle_text(chat_id, user, text)


def expire_questions() -> None:
    now = time.monotonic()
    expired_ids = [
        user_id for user_id, active in active_questions.items()
        if now > active.deadline
    ]
    for user_id in expired_ids:
        expire_question(user_id)


def main() -> None:
    telegram("deleteWebhook", {"drop_pending_updates": True})
    bot = telegram("getMe")
    print(f"Bot ishga tushdi: @{bot.get('username', 'unknown')}", flush=True)

    offset = 0
    while True:
        try:
            updates = telegram(
                "getUpdates",
                {
                    "offset": offset,
                    "timeout": POLL_SECONDS,
                    "allowed_updates": ["message"],
                },
            )
            for update in updates:
                offset = int(update["update_id"]) + 1
                try:
                    handle_update(update)
                except Exception as error:
                    print(f"Xabarni qayta ishlashda xato: {error}", flush=True)
            expire_questions()
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            print(f"Ulanishda xato: {error}. Qayta uriniladi.", flush=True)
            time.sleep(3)
        except Exception as error:
            print(f"Kutilmagan xato: {error}. Qayta uriniladi.", flush=True)
            time.sleep(3)


if __name__ == "__main__":
    main()
