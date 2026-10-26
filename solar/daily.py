"""Small daily delights: a drum break, a Thai phrase, a dinner question, album birthdays and some good news.

The curated lists rotate by day of the year, so everyone sees the same pick all day.
"""
import datetime as dt
import json
import re
import urllib.parse
import urllib.request

from . import news

UA = {"User-Agent": "solar-dashboard/1.0 (personal home dashboard)"}

# (song, artist, year, drummer or None, what to listen for)
DRUM_BREAKS = [
    ("Amen, Brother", "The Winstons", 1969, "G.C. Coleman", "Six seconds of drumming that became the most sampled break ever: jungle, drum and bass and countless hip-hop tracks."),
    ("Funky Drummer", "James Brown", 1970, "Clyde Stubblefield", "The ghost notes on the snare. Quiet hits between the backbeats that make the whole thing swing."),
    ("Cold Sweat", "James Brown", 1967, "Clyde Stubblefield", "Often called the record that invented funk. Listen to how the snare lands just off where you expect."),
    ("Get Up (I Feel Like Being a) Sex Machine", "James Brown", 1970, "John \"Jabo\" Starks", "Tight, simple and relentless. Starks proves you don't need many notes."),
    ("Apache", "Incredible Bongo Band", 1973, "Jim Gordon", "Bongos and a kit trading off. A cornerstone of early hip-hop block parties."),
    ("When the Levee Breaks", "Led Zeppelin", 1971, "John Bonham", "Recorded in a stairwell for that huge, booming room sound."),
    ("Fool in the Rain", "Led Zeppelin", 1979, "John Bonham", "A half-time shuffle with triplet feel. Bonham borrowed the idea from Purdie and made it his own."),
    ("Moby Dick", "Led Zeppelin", 1969, "John Bonham", "The drum solo showcase. Live, Bonham played part of it with his bare hands."),
    ("Good Times Bad Times", "Led Zeppelin", 1969, "John Bonham", "Those fast bass drum triplets, played with a single foot."),
    ("Rock Steady", "Aretha Franklin", 1971, "Bernard Purdie", "Purdie's pocket under Aretha: every hi-hat placed just right."),
    ("Home at Last", "Steely Dan", 1977, "Bernard Purdie", "The Purdie shuffle: a half-time groove full of ghosted snare triplets."),
    ("Babylon Sisters", "Steely Dan", 1980, "Bernard Purdie", "Another Purdie shuffle, slower and slinkier."),
    ("Aja", "Steely Dan", 1977, "Steve Gadd", "Gadd's solo near the end was reportedly done in a take or two. Session drumming at its peak."),
    ("50 Ways to Leave Your Lover", "Paul Simon", 1975, "Steve Gadd", "That marching, rudimental intro on snare and toms is one of the most copied grooves in pop."),
    ("Rosanna", "Toto", 1982, "Jeff Porcaro", "The Rosanna shuffle: a half-time shuffle with ghost notes, built on Purdie and Bonham."),
    ("Cissy Strut", "The Meters", 1969, "Zigaboo Modeliste", "New Orleans second-line feel turned into funk. Loose, behind the beat, perfect."),
    ("Look-Ka Py Py", "The Meters", 1969, "Zigaboo Modeliste", "Syncopation everywhere. The kick and snare dance around each other."),
    ("Hook and Sling", "Eddie Bo", 1969, "James Black", "A New Orleans drummer playing like a whole percussion section."),
    ("Chameleon", "Herbie Hancock", 1973, "Harvey Mason", "The Head Hunters groove: simple on top, busy and funky underneath."),
    ("Superstition", "Stevie Wonder", 1972, "Stevie Wonder", "Stevie played the drums himself. The hi-hat pattern alone is instantly recognizable."),
    ("Billie Jean", "Michael Jackson", 1982, "Leon \"Ndugu\" Chancler", "One of the most famous straight-ahead pop grooves. Nothing fancy, all feel."),
    ("Walk This Way", "Aerosmith", 1975, "Joey Kramer", "That opening beat later kicked off Run-DMC's version too."),
    ("Tom Sawyer", "Rush", 1981, "Neil Peart", "The fill into the instrumental section is air-drummed in cars everywhere."),
    ("YYZ", "Rush", 1981, "Neil Peart", "The intro rhythm spells YYZ, Toronto airport's code, in Morse code."),
    ("In the Air Tonight", "Phil Collins", 1981, "Phil Collins", "Wait for it: the most famous drum fill in pop, about 3:40 in."),
    ("Hot for Teacher", "Van Halen", 1984, "Alex Van Halen", "A double-bass drum intro that sounds like a revving engine."),
    ("Sunday Bloody Sunday", "U2", 1983, "Larry Mullen Jr.", "A military-style snare pattern that drives the whole song."),
    ("Smells Like Teen Spirit", "Nirvana", 1991, "Dave Grohl", "Those big tom fills after every line, played as hard as possible."),
    ("Take Five", "The Dave Brubeck Quartet", 1959, "Joe Morello", "Jazz in 5/4. Morello's solo makes an odd meter feel easy."),
    ("Sing, Sing, Sing", "Benny Goodman", 1937, "Gene Krupa", "The tom-tom pattern that made the drummer a star of the band."),
    ("Moanin'", "Art Blakey and the Jazz Messengers", 1958, "Art Blakey", "Blakey's press rolls push the band forward like a wave."),
    ("Footprints", "Miles Davis", 1967, "Tony Williams", "Tony Williams was barely 21 and already rewriting how jazz drums could move."),
    ("Seven Days", "Sting", 1993, "Vinnie Colaiuta", "A love song in 5/4 that never feels awkward, thanks to Colaiuta."),
]

# (Thai, romanization, meaning, tip or None)
THAI_PHRASES = [
    ("สวัสดี", "sa-wat-dee", "Hello / goodbye", "Add khrap (men) or kha (women) at the end to be polite."),
    ("ขอบคุณ", "khop khun", "Thank you", "Khop khun khrap / khop khun kha."),
    ("ไม่เป็นไร", "mai pen rai", "Never mind / no worries", "Maybe the most Thai phrase there is: let it go."),
    ("สบายดีไหม", "sa-bai dee mai", "How are you?", "Answer: sa-bai dee, I'm well."),
    ("กินข้าวหรือยัง", "gin khao rue yang", "Have you eaten yet?", "A common friendly greeting, not always a dinner invite."),
    ("อร่อย", "a-roi", "Delicious", "A-roi mak means very delicious."),
    ("เผ็ด", "phet", "Spicy", "Mai phet: not spicy. Phet nit noi: a little spicy."),
    ("เท่าไร", "tao rai", "How much?", "Point at it and say an-nee tao rai: how much is this?"),
    ("แพงไป", "phaeng pai", "Too expensive", "Smile when you say it. Bargaining is friendly at markets."),
    ("ลดหน่อยได้ไหม", "lot noi dai mai", "Can you lower the price a bit?", None),
    ("ห้องน้ำอยู่ที่ไหน", "hong nam yoo tee nai", "Where is the bathroom?", None),
    ("ใจเย็นๆ", "jai yen yen", "Calm down / take it easy", "Literally cool heart. Keeping a cool heart is a big Thai value."),
    ("สนุก", "sa-nuk", "Fun", "Sa-nuk is a whole outlook: life should be enjoyable."),
    ("ฝันดี", "fan dee", "Sweet dreams", None),
    ("โชคดี", "chok dee", "Good luck", "Also a warm way to say goodbye."),
    ("ยินดีที่ได้รู้จัก", "yin dee tee dai roo jak", "Nice to meet you", None),
    ("ไม่เข้าใจ", "mai khao jai", "I don't understand", None),
    ("พูดช้าๆ หน่อย", "phut cha cha noi", "Please speak slowly", None),
    ("พูดภาษาไทยได้นิดหน่อย", "phut pha-sa thai dai nit noi", "I speak a little Thai", "This one usually gets a big smile."),
    ("น้ำเปล่า", "nam plao", "Plain water", None),
    ("เช็คบิล", "chek bin", "Check, please", "Borrowed straight from English."),
    ("อิ่มแล้ว", "im laew", "I'm full", None),
    ("หิว", "hiu", "Hungry", "Hiu khao: hungry for rice, meaning hungry for a meal."),
    ("เหนื่อย", "nueai", "Tired", None),
    ("ร้อน", "ron", "Hot (weather)", "Ron mak: very hot. Useful in Bangkok."),
    ("หนาว", "nao", "Cold", "Handy for a Portland winter too."),
    ("ฝนตก", "fon tok", "It's raining", "Literally rain falls."),
    ("ทะเล", "ta-lay", "The sea", "Pai ta-lay: go to the beach."),
    ("ไปเที่ยว", "pai tiao", "Go out / take a trip", None),
    ("รักนะ", "rak na", "Love you", None),
    ("คิดถึง", "khit thueng", "Miss you", None),
    ("เก่งมาก", "keng mak", "Very good / so clever", "Great praise for your kid."),
    ("สุขสันต์วันเกิด", "suk san wan koet", "Happy birthday", None),
    ("ตลาด", "ta-lat", "Market", "Ta-lat nam: floating market."),
    ("ข้าวเหนียวมะม่วง", "khao niao ma-muang", "Mango sticky rice", None),
    ("กาแฟเย็น", "ka-fae yen", "Iced coffee", "Thai iced coffee is usually very sweet."),
    ("อากาศดี", "a-kat dee", "Nice weather", None),
    ("ช่วยด้วย", "chuay duay", "Help!", None),
]

DINNER_QUESTIONS = [
    "If you could have any animal as a pet, real or imaginary, what would it be?",
    "What was the best part of your day? What was the hardest part?",
    "If you could be invisible for one day, what would you do?",
    "What's something you learned this week that surprised you?",
    "If our family had a theme song, what would it be?",
    "Would you rather be able to fly or breathe underwater?",
    "If you could invent a new holiday, what would we celebrate?",
    "What's one thing you'd like to get better at this year?",
    "If you could eat only one food for a week, what would you pick?",
    "Who made you laugh today?",
    "If you could talk to one kind of animal, which would you choose?",
    "What would you do with a robot helper for a day?",
    "If you could visit any planet, which one and why?",
    "What's the kindest thing someone did for you lately?",
    "Would you rather live in a treehouse or an underwater house?",
    "If you could have any superpower for helping people, what would it be?",
    "What's a rule you'd make if you were in charge of the house for a day?",
    "If you wrote a book, what would it be about?",
    "What's your favorite sound?",
    "If you could switch places with anyone for a day, who would it be?",
    "If our house could talk, what would it say about us?",
    "Would you rather explore a jungle or a desert?",
    "If you could build anything out of LEGO at life size, what would it be?",
    "What's something you're proud of this week?",
    "If you had a time machine, would you go to the past or the future?",
    "What's the funniest dream you remember?",
    "If you could make one thing in the world free for everyone, what would it be?",
    "What would be the best and worst part of being a giant?",
    "If you started a band, what would it be called and what would you play?",
    "Which drum beat does your heart make when you're excited?",
    "If you could have dinner with any character from a book or movie, who would it be?",
    "What's a smell that makes you happy?",
    "If you could design a new ice cream flavor, what's in it?",
    "Would you rather have a dragon or be a dragon?",
    "What's something that's hard for you that might be easy for someone else, and the other way around?",
    "If you could change one thing about school, what would it be?",
    "Where would you go on our dream family trip?",
    "What's the best thing about being your age?",
    "If you could keep any wild animal as a friend for one day, what would you do together?",
    "What's one way you helped someone today?",
    "If you could grow anything in our garden, magic plants included, what would it be?",
    "Would you rather surf a giant wave or ski down a giant mountain?",
    "What would a perfect Saturday look like?",
    "If you were a teacher, what would you teach?",
    "What's something that made you curious today?",
    "If you could rename yourself for a week, what name would you pick?",
    "What do you think you'll be really good at when you grow up?",
    "If you could fill a room with anything, what would it be?",
    "What's your favorite thing about our family?",
    "If animals had jobs, what job would a raccoon have?",
    "Would you rather have a pocket-sized elephant or a giant hamster?",
    "What's a question you've always wanted to ask a grown-up?",
    "If you could see one dinosaur alive, which one?",
    "What's the coolest thing you've seen outside lately?",
    "If you could stay up all night once, what would you do?",
    "What would you put in a time capsule to open in 20 years?",
    "If you could make a new rule for the whole world, what would it be?",
    "Which would you rather visit: the bottom of the ocean or outer space?",
    "What's something new you'd like to try this month?",
    "Who is someone you want to say thank you to, and why?",
]


def _pick(items, day, salt=0):
    return items[(day.toordinal() * 7 + salt) % len(items)]

# (name, kind, why they matter, a good place to start). Portland and Oregon artists across music, art, books and film.
LOCAL_ARTISTS = [
    ("Esperanza Spalding", "music", "Jazz bassist and singer who grew up in NE Portland and beat Justin Bieber for Best New Artist at the 2011 Grammys.", "Chamber Music Society"),
    ("Pink Martini", "music", "Thomas Lauderdale's \"little orchestra\", started in Portland in 1994 to play political fundraisers. They now sing in over 20 languages.", "Sympathique"),
    ("Elliott Smith", "music", "Hushed, double-tracked songs written in Portland in the '90s. \"Miss Misery\" got him an Oscar nomination.", "Either/Or"),
    ("Sleater-Kinney", "music", "Corin Tucker and Carrie Brownstein's ferocious guitar band, a Portland institution since the '90s.", "Dig Me Out"),
    ("The Decemberists", "music", "Colin Meloy's bookish, sea-shanty-loving folk rock, with album art by Portland illustrator Carson Ellis.", "The Crane Wife"),
    ("Dead Moon", "music", "Fred and Toody Cole's raw, homemade garage punk, a Portland legend since 1987.", "Dead Moon Night"),
    ("Wipers", "music", "Greg Sage's dark, driving Portland punk from 1977. Kurt Cobain called them a huge influence.", "Youth of America"),
    ("The Kingsmen", "music", "Portland teenagers whose mumbled 1963 \"Louie Louie\" got the FBI to investigate the lyrics.", "Louie Louie"),
    ("Aminé", "music", "Playful NE Portland rapper who wears his city on his sleeve.", "Caroline"),
    ("Black Belt Eagle Scout", "music", "Katherine Paul's slow-burning indie rock, rooted in her Swinomish and Iñupiaq family.", "At the Party with My Brown Friends"),
    ("Haley Heynderickx", "music", "Portland songwriter with intricate fingerpicking and a lot of heart.", "Oom Sha La La"),
    ("Y La Bamba", "music", "Luz Elena Mendoza's dreamy blend of Mexican folk and indie rock.", "Entre Los Dos"),
    ("Unknown Mortal Orchestra", "music", "Ruban Nielson's woozy psych-funk, recorded in his Portland basement.", "Multi-Love"),
    ("Laura Veirs", "music", "Portland folk songwriter, also one third of case/lang/veirs.", "July Flame"),
    ("M. Ward", "music", "Warm, vintage-sounding guitarist and songwriter, also half of She & Him.", "Post-War"),
    ("Typhoon", "music", "Kyle Morton's Portland orchestra-sized band making huge, horn-filled songs about being alive.", "White Lighter"),
    ("Blind Pilot", "music", "Portland folk band that toured the West Coast by bicycle in its early days.", "3 Rounds and a Sound"),
    ("Thara Memory", "music", "Portland trumpeter and teacher who mentored a young Esperanza Spalding and won a Grammy arranging her \"City of Roses\".", "City of Roses"),
    ("Mel Brown", "music", "Portland jazz drummer who played Motown sessions, then held down a weekly residency at Jimmy Mak's for decades.", "Mel Brown Septet"),
    ("The Dandy Warhols", "music", "Portland's swaggering '90s psych-rockers. \"Bohemian Like You\" was everywhere in 2001.", "Bohemian Like You"),
    ("Quasi", "music", "Sam Coomes and Janet Weiss's two-person noise-pop band.", "Featuring \"Birds\""),
    ("Portugal. The Man", "music", "Alaskan transplants who made Portland home and won a Grammy with \"Feel It Still\".", "Feel It Still"),
    ("Storm Large", "music", "Powerhouse cabaret-rock singer and sometime Pink Martini vocalist.", "Le Bonheur"),
    ("Mark Rothko", "art", "Grew up in Portland after arriving from Russia at 10, graduated from Lincoln High, then went on to paint the glowing color fields.", "Rothko at the Portland Art Museum"),
    ("Carrie Mae Weems", "photography", "Born in Portland in 1953. Her Kitchen Table Series is one of the great works of American photography.", "Kitchen Table Series"),
    ("Marie Watt", "art", "Seneca artist in Portland who builds towers and quilts out of donated wool blankets and the stories that come with them.", "Marie Watt blanket towers"),
    ("Wendy Red Star", "photography", "Apsáalooke (Crow) artist in Portland who restages and annotates 19th-century portraits with sharp wit.", "1880 Crow Peace Delegation"),
    ("Lillian Pitt", "art", "Warm Springs, Wasco and Yakama artist whose masks and bronzes honor Columbia River ancestors.", "Lillian Pitt Columbia River art"),
    ("Rick Bartow", "art", "Wiyot artist from Newport, Oregon, known for gestural animals and the giant carved poles \"We Were Always Here\" at the Smithsonian.", "We Were Always Here"),
    ("Arvie Smith", "art", "Portland painter whose bright, satirical canvases take on racist imagery and American history.", "Arvie Smith paintings"),
    ("Isaka Shamsud-Din", "art", "Painter and muralist who has documented Black Portland and the Albina neighborhood since the 1960s.", "Isaka Shamsud-Din murals"),
    ("Hilda Morris", "art", "Mid-century Portland sculptor. You've probably walked past her bronze \"Ring of Time\" downtown.", "Ring of Time"),
    ("Carson Ellis", "illustration", "Illustrator behind the Decemberists' covers and the Caldecott Honor book \"Du Iz Tak?\", a great one to read with your kid.", "Du Iz Tak?"),
    ("Craig Thompson", "comics", "Portland cartoonist behind \"Blankets\", a huge, tender graphic memoir about first love.", "Blankets"),
    ("Will Vinton", "animation", "Coined the word \"Claymation\" and brought the California Raisins to life from his Portland studio.", "Closed Mondays"),
    ("Gus Van Sant", "film", "Filmed Portland's underbelly in \"Drugstore Cowboy\" and \"My Own Private Idaho\".", "My Own Private Idaho"),
    ("Matt Groening", "comics", "Grew up in Portland. Flanders, Lovejoy, Kearney and Quimby are all Portland street names.", "Life in Hell"),
    ("Ursula K. Le Guin", "books", "Portland's great writer of science fiction and fantasy, and a fierce essayist.", "The Left Hand of Darkness"),
    ("Beverly Cleary", "books", "Grew up in Portland. Ramona lives on the real Klickitat Street, and her statue stands in Grant Park.", "Ramona the Pest"),
    ("Mitchell S. Jackson", "books", "Grew up in NE Portland and won the 2021 Pulitzer Prize for feature writing.", "Survival Math"),
    ("Cheryl Strayed", "books", "Portland writer whose Pacific Crest Trail memoir ends at the Bridge of the Gods.", "Wild"),
    ("Brian Doyle", "books", "Portland essayist with joyful, run-on sentences, and editor of the University of Portland's magazine.", "Mink River"),
    ("Chuck Palahniuk", "books", "Portland-area novelist who wrote \"Fight Club\" while working as a diesel mechanic.", "Fight Club"),
]

ARTIST_VERB = {"music": ("▶ Listen", "🎸"), "film": ("▶ Watch", "🎬"), "animation": ("▶ Watch", "🎞️"),
               "books": ("Read about it", "📚"), "comics": ("Read about it", "💬"), "illustration": ("See the work", "🖍️"),
               "photography": ("See the work", "📷"), "art": ("See the work", "🎨")}


def local_artist(day):
    name, kind, note, start = _pick(LOCAL_ARTISTS, day, 4)
    verb, icon = ARTIST_VERB.get(kind, ("Look", "✨"))
    q = f"{name} {start}" if start.lower() not in name.lower() and name.lower() not in start.lower() else start
    url = ("https://www.youtube.com/results?" + urllib.parse.urlencode({"search_query": q}) if kind in ("music", "film", "animation")
           else "https://duckduckgo.com/?" + urllib.parse.urlencode({"q": q}))
    return {"name": name, "kind": kind, "note": note, "start": start, "url": url, "verb": verb, "icon": icon}


def picks(day):
    """Today's drum break, Thai phrase and dinner question."""
    song, artist, year, drummer, note = _pick(DRUM_BREAKS, day, 1)
    thai, roman, meaning, tip = _pick(THAI_PHRASES, day, 2)
    return {
        "drum": {"song": song, "artist": artist, "year": year, "drummer": drummer, "note": note,
                 "listen": "https://www.youtube.com/results?" + urllib.parse.urlencode({"search_query": f"{artist} {song}"})},
        "thai": {"thai": thai, "roman": roman, "meaning": meaning, "tip": tip},
        "question": _pick(DINNER_QUESTIONS, day, 3),
        "artist": local_artist(day),
    }


ALBUM_QUERY = """
SELECT ?album ?albumLabel ?artistLabel ?date ?links WHERE {
  VALUES ?type { wd:Q482994 wd:Q208569 }
  ?album wdt:P31 ?type; p:P577 [ psv:P577 [ wikibase:timeValue ?date; wikibase:timePrecision 11 ] ];
         wdt:P175 ?artist; wikibase:sitelinks ?links.
  FILTER(?links >= 15)
  FILTER(MONTH(?date) = %d && DAY(?date) = %d)
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY DESC(?links) LIMIT 40
"""


def album_birthdays(day, n=8):
    """Well-known albums released on this date in past years, from Wikidata, most-written-about first."""
    url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode(
        {"query": ALBUM_QUERY % (day.month, day.day), "format": "json"})
    req = urllib.request.Request(url, headers={**UA, "Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        rows = json.load(r)["results"]["bindings"]
    out, seen = [], set()
    for b in rows:
        title, artist = b["albumLabel"]["value"], b["artistLabel"]["value"]
        year = int(b["date"]["value"][:4])
        if title in seen or re.fullmatch(r"Q\d+", title) or re.fullmatch(r"Q\d+", artist) or year >= day.year:
            continue
        seen.add(title)
        out.append({"title": title, "artist": artist, "year": year, "age": day.year - year,
                    "url": b["album"]["value"].replace("http://", "https://")})
        if len(out) >= n:
            break
    return {"date": day.isoformat(), "albums": out}


GOOD_SOURCES = [
    ("Oregon", ["https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": '(Portland OR Oregon) (volunteers OR rescued OR donated OR "good news" OR heartwarming OR celebrates OR restored)',
         "hl": "en-US", "gl": "US", "ceid": "US:en"})]),
    ("Good News Network", ["https://www.goodnewsnetwork.org/feed/"]),
    ("Positive News", ["https://www.positive.news/feed/"]),
    ("Reasons to be Cheerful", ["https://reasonstobecheerful.world/feed/"]),
]
GLOOM = re.compile(r"\b(kill|killed|dies|died|dead|death|shoot|shooting|shot|crash|arrest|charged|lawsuit|sued|"
                   r"fire|fraud|abuse|missing|attack|war|murder|stabb|injur|victim|overdose|scam|trump|election)", re.I)
LOCAL = re.compile(r"\b(portland|oregon|pdx|multnomah|sauvie|columbia river|gorge|astoria|seaside|beaverton|gresham)\b", re.I)


def good_news(n=3):
    """A few upbeat stories, Oregon ones first."""
    items, failed = news._collect(GOOD_SOURCES, 4)
    keep = []
    for it in items:
        title = it["title"]
        if it["source"] == "Oregon" and " - " in title:
            title, _, outlet = title.rpartition(" - ")
            it = {**it, "title": title, "outlet": outlet}
        if GLOOM.search(title + " " + it.get("summary", "")):
            continue
        it["local"] = bool(LOCAL.search(title + " " + it.get("summary", "")))
        if it["source"] == "Oregon" and not it["local"]:
            continue
        keep.append(it)
    keep = sorted(keep, key=lambda x: (not x["local"], -dt.datetime.fromisoformat(x["utc"]).timestamp()))
    out, titles = [], set()
    for it in keep:
        key = it["title"].lower()[:60]
        if key in titles:
            continue
        titles.add(key)
        out.append({"title": it["title"], "url": it["url"], "source": it.get("outlet") or it["source"],
                    "summary": "" if it["source"] == "Oregon" else it.get("summary", ""),
                    "image": it.get("image"), "local": it["local"], "utc": it["utc"]})
        if len(out) >= n:
            break
    if not out:
        raise RuntimeError("no good news feeds answered (" + ", ".join(failed) + ")")
    return out
