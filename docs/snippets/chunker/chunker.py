#from utils.chunker.download_data import ensure_punkt


# text_en = "Hello world. This is an English sentence. NLTK can split sentences easily!"
# chunks_en = chunk_text(text_en, language="english")

# print("English chunks:", chunks_en)

# text_ar = "السلام عليكم. وبالسياره هنا نتكلم"
# chunks_ar = chunk_text(text_ar, language="arabic")


# print("Arabic chunks:", chunks_ar)

# text_ru = "Иску́сственный интелле́кт или ИИ, Искусственный разум (англ. artificial intelligence; AI) в самом широком смысле — это интеллект, демонстрируемый машинами, в частности компьютерными системами. Это область исследований в области компьютерных наук, которая разрабатывает и изучает методы и программное обеспечение, позволяющие машинам воспринимать окружающую среду и использовать обучение и интеллект для выполнения действий, которые максимально увеличивают их шансы на достижение поставленных целей[3]. Такие машины можно назвать искусственным интеллектом. Некоторые из наиболее известных приложений искусственного интеллекта включают в себя передовые поисковые системы (например, Google Search, Bing, Яндекс); рекомендательные системы (используемые на YouTube, Amazon и Netflix); взаимодействие посредством человеческой речи (например, Google Assistant, Siri, Alexa, Алиса); автономные транспортные средства (например, Waymo); генеративные и творческие инструменты (например, ChatGPT, Apple Intelligence и искусство искусственного интеллекта); а также сверхчеловеческую игру и анализ в стратегических играх (например, шахматы и го). Однако многие приложения искусственного интеллекта не воспринимаются как искусственный интеллект: «Многие передовые разработки искусственного интеллекта проникли в общие приложения, часто не называясь искусственным интеллектом, потому что как только что-то становится достаточно полезным и достаточно распространённым, его больше не называют искусственным интеллектом»[4][5]. Алан Тьюринг был первым человеком, который провёл масштабные исследования в области, которую он назвал машинным интеллектом[6]. Искусственный интеллект был основан как академическая дисциплина в 1956 году[7] теми, кого сейчас считают отцами-основателями искусственного интеллекта: Джоном Маккарти, Марвином Мински, Натаниэлем Рочестером и Клодом Шенноном[8][9]. Эта область пережила несколько циклов оптимизма[10], за которыми последовали периоды разочарования и потери финансирования, известные как зима искусственного интеллекта[11]. Финансирование и интерес значительно возросли после 2012 года, когда глубокое обучение превзошло все предыдущие методы искусственного интеллекта[12], а также после 2017 года с появлением архитектуры Transformer. Это привело к буму искусственного интеллекта в начале 2020-х годов, когда компании, университеты и лаборатории, в подавляющем большинстве базирующиеся в Соединённых Штатах, стали пионерами значительных достижений в области искусственного интеллекта. Растущее использование искусственного интеллекта в XXI веке влияет на общественный и экономический сдвиг в сторону большей автоматизации, принятия решений на основе данных и интеграции систем искусственного интеллекта в различные секторы экономики и сферы жизни, влияя на рынки труда, здравоохранение, государственное управление, промышленность, образование, пропаганду и дезинформацию. Это поднимает вопросы о долгосрочных эффектах, этических последствиях и рисках искусственного интеллекта, побуждая к обсуждениям о политике регулирования, направленной на обеспечение безопасности и преимуществ этой технологии. Различные направления исследований искусственного интеллекта сосредоточены вокруг определённых целей и использования определённых инструментов. Традиционные цели исследований искусственного интеллекта включают рассуждение, представление знаний, планирование, обучение, обработку естественного языка, восприятие и поддержку робототехники[13]. Общий интеллект, или же сильный, — способность выполнять любую задачу, которую может выполнить человек, по крайней мере на равном уровне — входит в число долгосрочных целей данной области[14].Для достижения этих целей исследователи искусственного интеллекта адаптировали и интегрировали широкий спектр методов, включая поиск и математическую оптимизацию, формальную логику, искусственные нейронные сети, а также методы, основанные на статистике, исследовании операций и экономике[13]. Искусственный интеллект также опирается на психологию, лингвистику, философию, нейронауку и другие области[15].."

# chunks_ru = chunk_text(text_ru, language="russian")

# for index, chunk in chunks_ru:
#     print(f"Chunk {index}: {chunk}")

# note = "Hello world. This is a test note. It has several sentences. Enough to split."
# chunks = chunk_text(note, chunk_size=800)

# for index, chunk in chunks:
#     print(f"Chunk {index}: {chunk}")
#ensure_punkt()
# text = "السلام عليكم. وبالسياره هنا نتكلم"
# chunks = chunk_text(text, chunk_size=10, language="arabic")

# for c in chunks:
#     print(f"Chunk {c[0]}: {c[1]}")

from utils.chunker.chunk_sentence import chunk_text

content = """
The downloader will search for an existing nltk_data directory to install NLTK data. If one does not exist it will attempt to create one in a central location (when using an administrator account) or otherwise in the user’s filespace. If necessary, run the download command from an administrator account, or using sudo. The recommended system location is C:\nltk_data (Windows); /usr/local/share/nltk_data (Mac); and /usr/share/nltk_data (Unix). You can use the -d flag to specify a different location (but if you do this, be sure to set the NLTK_DATA environment variable accordingly).

Run the command python -m nltk.downloader all. To ensure central installation, run the command sudo python -m nltk.downloader -d /usr/local/share/nltk_data all.

Windows: Use the “Run…” option on the Start menu. Windows Vista users need to first turn on this option, using Start -> Properties -> Customize to check the box to activate the “Run…” option.

Test the installation: Check that the user environment and privileges are set correctly by logging in to a user account, starting the Python interpreter, and accessing the Brown Corpus (see the previous section).

Manual installation
Create a folder nltk_data, e.g. C:\nltk_data, or /usr/local/share/nltk_data, and subfolders chunkers, grammars, misc, sentiment, taggers, corpora, help, models, stemmers, tokenizers.

Download individual packages from https://www.nltk.org/nltk_data/ (see the “download” links). Unzip them to the appropriate subfolder. For example, the Brown Corpus, found at: https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/brown.zip is to be unzipped to nltk_data/corpora/brown.

Set your NLTK_DATA environment variable to point to your top level nltk_data folder.
"""


 # 1. Split content into semantic chunks
chunks = chunk_text(content, chunk_size=50, overlap=5)
title = "My English Note"
tags = ["english", "nltk", "chunking"]
    # 2. Build inputs (text for embedding)
inputs = [
        f"Title: {title}\nTags: {', '.join(tags)}\n{c}"
        for c in chunks
    ]

#print(inputs)

metadatas = [
        {
            "note_id": "note_12300",
            "chunk_index": i,
            "notebook_id": "notebook_45600",
            "user_id": "user_78900",
            "title": title,
            "tags": tags,
            "is_archived": True,
            "is_pinned": True,
            "reminders": [],
            "created_at": "2023-10-01T12:00:00Z",
            "updated_at": "2023-10-01T12:00:00Z",
            "version": 1,
        }
        for i in range(len(chunks))
    ]

    # 4. Build ids for Chroma
ids = [f"note_12300_{i}" for i in range(len(chunks))]

print(ids)
print("=="*50)
print(metadatas[3])