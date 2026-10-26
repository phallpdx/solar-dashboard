"""A famous poem that fits the day: a holiday first, then today's weather, then the season.

Every poem here is in the public domain, so the text can sit on a public page.
"""
import datetime as dt
import urllib.parse

# key: (title, poet, year, text, excerpt?)
POEMS = {
    "dreamwithin": ("A Dream Within a Dream", "Edgar Allan Poe", 1849, """Take this kiss upon the brow!
And, in parting from you now,
Thus much let me avow —
You are not wrong, who deem
That my days have been a dream;
Yet if hope has flown away
In a night, or in a day,
In a vision, or in none,
Is it therefore the less gone?
All that we see or seem
Is but a dream within a dream.

I stand amid the roar
Of a surf-tormented shore,
And I hold within my hand
Grains of the golden sand —
How few! yet how they creep
Through my fingers to the deep,
While I weep — while I weep!
O God! Can I not grasp
Them with a tighter clasp?
O God! can I not save
One from the pitiless wave?
Is all that we see or seem
But a dream within a dream?""", False),
    "alone": ("Alone", "Edgar Allan Poe", 1829, """From childhood's hour I have not been
As others were—I have not seen
As others saw—I could not bring
My passions from a common spring—
From the same source I have not taken
My sorrow—I could not awaken
My heart to joy at the same tone—
And all I lov'd—I lov'd alone—
Then—in my childhood—in the dawn
Of a most stormy life—was drawn
From ev'ry depth of good and ill
The mystery which binds me still—
From the torrent, or the spring—
From the red cliff of the mountain—
From the sun that 'round me roll'd
In its autumn tint of gold—
From the lightning in the sky
As it pass'd me flying by—
From the thunder, and the storm—
And the cloud that took the form
(When the rest of Heaven was blue)
Of a demon in my view—""", False),
    "raven": ("The Raven", "Edgar Allan Poe", 1845, """Once upon a midnight dreary, while I pondered, weak and weary,
Over many a quaint and curious volume of forgotten lore—
While I nodded, nearly napping, suddenly there came a tapping,
As of some one gently rapping, rapping at my chamber door.
"'Tis some visitor," I muttered, "tapping at my chamber door—
Only this and nothing more.\"""", True),
    "death": ("Because I could not stop for Death", "Emily Dickinson", 1890, """Because I could not stop for Death –
He kindly stopped for me –
The Carriage held but just Ourselves –
And Immortality.

We slowly drove – He knew no haste
And I had put away
My labor and my leisure too,
For His Civility –

We passed the School, where Children strove
At Recess – in the Ring –
We passed the Fields of Gazing Grain –
We passed the Setting Sun –""", True),
    "colossus": ("The New Colossus", "Emma Lazarus", 1883, """Not like the brazen giant of Greek fame,
With conquering limbs astride from land to land;
Here at our sea-washed, sunset gates shall stand
A mighty woman with a torch, whose flame
Is the imprisoned lightning, and her name
Mother of Exiles. From her beacon-hand
Glows world-wide welcome; her mild eyes command
The air-bridged harbor that twin cities frame.
"Keep, ancient lands, your storied pomp!" cries she
With silent lips. "Give me your tired, your poor,
Your huddled masses yearning to breathe free,
The wretched refuse of your teeming shore.
Send these, the homeless, tempest-tost to me,
I lift my lamp beside the golden door!\"""", False),
    "flanders": ("In Flanders Fields", "John McCrae", 1915, """In Flanders fields the poppies blow
Between the crosses, row on row,
That mark our place; and in the sky
The larks, still bravely singing, fly
Scarce heard amid the guns below.

We are the Dead. Short days ago
We lived, felt dawn, saw sunset glow,
Loved and were loved, and now we lie,
In Flanders fields.

Take up our quarrel with the foe:
To you from failing hands we throw
The torch; be yours to hold it high.
If ye break faith with us who die
We shall not sleep, though poppies grow
In Flanders fields.""", False),
    "river": ("Over the River and Through the Wood", "Lydia Maria Child", 1844, """Over the river, and through the wood,
To grandfather's house we go;
The horse knows the way
To carry the sleigh
Through the white and drifted snow.

Over the river, and through the wood—
Oh, how the wind does blow!
It stings the toes
And bites the nose,
As over the ground we go.""", True),
    "midwinter": ("In the Bleak Midwinter", "Christina Rossetti", 1872, """In the bleak mid-winter
Frosty wind made moan,
Earth stood hard as iron,
Water like a stone;
Snow had fallen, snow on snow,
Snow on snow,
In the bleak mid-winter
Long ago.""", True),
    "langsyne": ("Auld Lang Syne", "Robert Burns", 1788, """Should auld acquaintance be forgot,
And never brought to mind?
Should auld acquaintance be forgot,
And auld lang syne?

For auld lang syne, my dear,
For auld lang syne.
We'll tak a cup o' kindness yet,
For auld lang syne.""", True),
    "bells": ("Ring Out, Wild Bells", "Alfred, Lord Tennyson", 1850, """Ring out, wild bells, to the wild sky,
The flying cloud, the frosty light:
The year is dying in the night;
Ring out, wild bells, and let him die.

Ring out the old, ring in the new,
Ring, happy bells, across the snow:
The year is going, let him go;
Ring out the false, ring in the true.""", True),
    "dreams": ("Dreams", "Langston Hughes", 1923, """Hold fast to dreams
For if dreams die
Life is a broken-winged bird
That cannot fly.

Hold fast to dreams
For when dreams go
Life is a barren field
Frozen with snow.""", False),
    "itoo": ("I, Too", "Langston Hughes", 1926, """I, too, sing America.

I am the darker brother.
They send me to eat in the kitchen
When company comes,
But I laugh,
And eat well,
And grow strong.

Tomorrow,
I'll be at the table
When company comes.
Nobody'll dare
Say to me,
"Eat in the kitchen,"
Then.

Besides,
They'll see how beautiful I am
And be ashamed—

I, too, am America.""", False),
    "sympathy": ("Sympathy", "Paul Laurence Dunbar", 1899, """I know what the caged bird feels, alas!
When the sun is bright on the upland slopes;
When the wind stirs soft through the springing grass,
And the river flows like a stream of glass;
When the first bird sings and the first bud opes,
And the faint perfume from its chalice steals—
I know what the caged bird feels!""", True),
    "countways": ("How Do I Love Thee? (Sonnet 43)", "Elizabeth Barrett Browning", 1850, """How do I love thee? Let me count the ways.
I love thee to the depth and breadth and height
My soul can reach, when feeling out of sight
For the ends of being and ideal grace.
I love thee to the level of every day's
Most quiet need, by sun and candle-light.
I love thee freely, as men strive for right.
I love thee purely, as they turn from praise.
I love thee with the passion put to use
In my old griefs, and with my childhood's faith.
I love thee with a love I seemed to lose
With my lost saints. I love thee with the breath,
Smiles, tears, of all my life; and, if God choose,
I shall but love thee better after death.""", False),
    "sonnet18": ("Shall I compare thee to a summer's day? (Sonnet 18)", "William Shakespeare", 1609, """Shall I compare thee to a summer's day?
Thou art more lovely and more temperate:
Rough winds do shake the darling buds of May,
And summer's lease hath all too short a date;
Sometime too hot the eye of heaven shines,
And often is his gold complexion dimm'd;
And every fair from fair sometime declines,
By chance or nature's changing course untrimm'd;
But thy eternal summer shall not fade,
Nor lose possession of that fair thou ow'st;
Nor shall Death brag thou wander'st in his shade,
When in eternal lines to time thou grow'st:
So long as men can breathe or eyes can see,
So long lives this, and this gives life to thee.""", False),
    "america": ("I Hear America Singing", "Walt Whitman", 1860, """I hear America singing, the varied carols I hear,
Those of mechanics, each one singing his as it should be blithe and strong,
The carpenter singing his as he measures his plank or beam,
The mason singing his as he makes ready for work, or leaves off work,
The boatman singing what belongs to him in his boat, the deckhand singing on the steamboat deck,
The shoemaker singing as he sits on his bench, the hatter singing as he stands,
The wood-cutter's song, the ploughboy's on his way in the morning, or at noon intermission or at sundown,
The delicious singing of the mother, or of the young wife at work, or of the girl sewing or washing,
Each singing what belongs to him or her and to none else,
The day what belongs to the day—at night the party of young fellows, robust, friendly,
Singing with open mouths their strong melodious songs.""", False),
    "pied": ("Pied Beauty", "Gerard Manley Hopkins", 1877, """Glory be to God for dappled things—
For skies of couple-colour as a brinded cow;
For rose-moles all in stipple upon trout that swim;
Fresh-firecoal chestnut-falls; finches' wings;
Landscape plotted and pieced—fold, fallow, and plough;
And all trades, their gear and tackle and trim.

All things counter, original, spare, strange;
Whatever is fickle, freckled (who knows how?)
With swift, slow; sweet, sour; adazzle, dim;
He fathers-forth whose beauty is past change:
Praise him.""", False),
    "rainyday": ("The Rainy Day", "Henry Wadsworth Longfellow", 1842, """The day is cold, and dark, and dreary;
It rains, and the wind is never weary;
The vine still clings to the mouldering wall,
But at every gust the dead leaves fall,
And the day is dark and dreary.

My life is cold, and dark, and dreary;
It rains, and the wind is never weary;
My thoughts still cling to the mouldering Past,
But the hopes of youth fall thick in the blast,
And the days are dark and dreary.

Be still, sad heart! and cease repining;
Behind the clouds is the sun still shining;
Thy fate is the common fate of all,
Into each life some rain must fall,
Some days must be dark and dreary.""", False),
    "softrains": ("There Will Come Soft Rains", "Sara Teasdale", 1918, """There will come soft rains and the smell of the ground,
And swallows circling with their shimmering sound;

And frogs in the pools singing at night,
And wild plum trees in tremulous white;

Robins will wear their feathery fire,
Whistling their whims on a low fence-wire;

And not one will know of the war, not one
Will care at last when it is done.

Not one would mind, neither bird nor tree,
If mankind perished utterly;

And Spring herself, when she woke at dawn
Would scarcely know that we were gone.""", False),
    "wheelbarrow": ("The Red Wheelbarrow", "William Carlos Williams", 1923, """so much depends
upon

a red wheel
barrow

glazed with rain
water

beside the white
chickens""", False),
    "rain": ("Rain", "Robert Louis Stevenson", 1885, """The rain is raining all around,
It falls on field and tree,
It rains on the umbrellas here,
And on the ships at sea.""", False),
    "fog": ("Fog", "Carl Sandburg", 1916, """The fog comes
on little cat feet.

It sits looking
over harbor and city
on silent haunches
and then moves on.""", False),
    "wind": ("Who Has Seen the Wind?", "Christina Rossetti", 1872, """Who has seen the wind?
Neither I nor you:
But when the leaves hang trembling,
The wind is passing through.

Who has seen the wind?
Neither you nor I:
But when the trees bow down their heads,
The wind is passing by.""", False),
    "hope": ('"Hope" is the thing with feathers', "Emily Dickinson", 1891, """"Hope" is the thing with feathers -
That perches in the soul -
And sings the tune without the words -
And never stops - at all -

And sweetest - in the Gale - is heard -
And sore must be the storm -
That could abash the little Bird
That kept so many warm -

I've heard it in the chillest land -
And on the strangest Sea -
Yet - never - in Extremity,
It asked a crumb - of me.""", False),
    "woods": ("Stopping by Woods on a Snowy Evening", "Robert Frost", 1923, """Whose woods these are I think I know.
His house is in the village though;
He will not see me stopping here
To watch his woods fill up with snow.

My little horse must think it queer
To stop without a farmhouse near
Between the woods and frozen lake
The darkest evening of the year.

He gives his harness bells a shake
To ask if there is some mistake.
The only other sound's the sweep
Of easy wind and downy flake.

The woods are lovely, dark and deep,
But I have promises to keep,
And miles to go before I sleep,
And miles to go before I sleep.""", False),
    "dust": ("Dust of Snow", "Robert Frost", 1923, """The way a crow
Shook down on me
The dust of snow
From a hemlock tree

Has given my heart
A change of mood
And saved some part
Of a day I had rued.""", False),
    "fireice": ("Fire and Ice", "Robert Frost", 1920, """Some say the world will end in fire,
Some say in ice.
From what I've tasted of desire
I hold with those who favor fire.
But if it had to perish twice,
I think I know enough of hate
To say that for destruction ice
Is also great
And would suffice.""", False),
    "gold": ("Nothing Gold Can Stay", "Robert Frost", 1923, """Nature's first green is gold,
Her hardest hue to hold.
Her early leaf's a flower;
But only so an hour.
Then leaf subsides to leaf.
So Eden sank to grief,
So dawn goes down to day.
Nothing gold can stay.""", False),
    "road": ("The Road Not Taken", "Robert Frost", 1916, """Two roads diverged in a yellow wood,
And sorry I could not travel both
And be one traveler, long I stood
And looked down one as far as I could
To where it bent in the undergrowth;

Then took the other, as just as fair,
And having perhaps the better claim,
Because it was grassy and wanted wear;
Though as for that the passing there
Had worn them really about the same,

And both that morning equally lay
In leaves no step had trodden black.
Oh, I kept the first for another day!
Yet knowing how way leads on to way,
I doubted if I should ever come back.

I shall be telling this with a sigh
Somewhere ages and ages hence:
Two roads diverged in a wood, and I—
I took the one less traveled by,
And that has made all the difference.""", False),
    "autumn": ("To Autumn", "John Keats", 1820, """Season of mists and mellow fruitfulness,
Close bosom-friend of the maturing sun;
Conspiring with him how to load and bless
With fruit the vines that round the thatch-eves run;
To bend with apples the moss'd cottage-trees,
And fill all fruit with ripeness to the core;
To swell the gourd, and plump the hazel shells
With a sweet kernel; to set budding more,
And still more, later flowers for the bees,
Until they think warm days will never cease,
For summer has o'er-brimm'd their clammy cells.""", True),
    "goldengrove": ("Spring and Fall", "Gerard Manley Hopkins", 1880, """Margaret, are you grieving
Over Goldengrove unleaving?
Leaves, like the things of man, you
With your fresh thoughts care for, can you?
Ah! as the heart grows older
It will come to such sights colder
By and by, nor spare a sigh
Though worlds of wanwood leafmeal lie;
And yet you will weep and know why.
Now no matter, child, the name:
Sorrow's springs are the same.
Nor mouth had, no nor mind, expressed
What heart heard of, ghost guessed:
It is the blight man was born for,
It is Margaret you mourn for.""", False),
    "daffodils": ("I Wandered Lonely as a Cloud", "William Wordsworth", 1807, """I wandered lonely as a cloud
That floats on high o'er vales and hills,
When all at once I saw a crowd,
A host, of golden daffodils;
Beside the lake, beneath the trees,
Fluttering and dancing in the breeze.

Continuous as the stars that shine
And twinkle on the milky way,
They stretched in never-ending line
Along the margin of a bay:
Ten thousand saw I at a glance,
Tossing their heads in sprightly dance.""", True),
    "innisfree": ("The Lake Isle of Innisfree", "W. B. Yeats", 1890, """I will arise and go now, and go to Innisfree,
And a small cabin build there, of clay and wattles made;
Nine bean-rows will I have there, a hive for the honey-bee,
And live alone in the bee-loud glade.

And I shall have some peace there, for peace comes dropping slow,
Dropping from the veils of the morning to where the cricket sings;
There midnight's all a glimmer, and noon a purple glow,
And evening full of the linnet's wings.

I will arise and go now, for always night and day
I hear lake water lapping with low sounds by the shore;
While I stand on the roadway, or on the pavements grey,
I hear it in the deep heart's core.""", False),
    "astronomer": ("When I Heard the Learn'd Astronomer", "Walt Whitman", 1865, """When I heard the learn'd astronomer,
When the proofs, the figures, were ranged in columns before me,
When I was shown the charts and diagrams, to add, divide, and measure them,
When I sitting heard the astronomer where he lectured with much applause in the lecture-room,
How soon unaccountable I became tired and sick,
Till rising and gliding out I wander'd off by myself,
In the mystical moist night-air, and from time to time,
Look'd up in perfect silence at the stars.""", False),
    "ozymandias": ("Ozymandias", "Percy Bysshe Shelley", 1818, """I met a traveller from an antique land,
Who said—"Two vast and trunkless legs of stone
Stand in the desert. . . . Near them, on the sand,
Half sunk a shattered visage lies, whose frown,
And wrinkled lip, and sneer of cold command,
Tell that its sculptor well those passions read
Which yet survive, stamped on these lifeless things,
The hand that mocked them, and the heart that fed;
And on the pedestal, these words appear:
My name is Ozymandias, King of Kings;
Look on my Works, ye Mighty, and despair!
Nothing beside remains. Round the decay
Of that colossal Wreck, boundless and bare
The lone and level sands stretch far away.\"""", False),
}


def _nth_weekday(year, month, weekday, n):
    """n-th weekday (Mon=0) of a month; n=-1 for the last one."""
    if n > 0:
        first = dt.date(year, month, 1)
        return first + dt.timedelta(days=(weekday - first.weekday()) % 7 + 7 * (n - 1))
    last = (dt.date(year, month % 12 + 1, 1) if month < 12 else dt.date(year + 1, 1, 1)) - dt.timedelta(days=1)
    return last - dt.timedelta(days=(last.weekday() - weekday) % 7)


def _occasions(day):
    """(first day, last day, reason, poem keys), narrowest windows win."""
    y = day.year
    d = lambda m, dd: dt.date(y, m, dd)
    mlk, labor = _nth_weekday(y, 1, 0, 3), _nth_weekday(y, 9, 0, 1)
    memorial, thanks = _nth_weekday(y, 5, 0, -1), _nth_weekday(y, 11, 3, 4)
    return [
        (d(1, 1), d(1, 2), "A new year", ["bells"]),
        (mlk - dt.timedelta(days=1), mlk, "Martin Luther King Jr. Day", ["dreams"]),
        (d(2, 1), d(2, 29) if y % 4 == 0 else d(2, 28), "Black History Month", ["itoo", "sympathy", "dreams"]),
        (d(2, 13), d(2, 14), "Valentine's Day", ["countways"]),
        (d(4, 22), d(4, 22), "Earth Day", ["pied"]),
        (memorial - dt.timedelta(days=2), memorial, "Memorial Day weekend", ["flanders"]),
        (d(6, 19), d(6, 19), "Juneteenth", ["sympathy"]),
        (d(6, 20), d(6, 21), "The summer solstice", ["sonnet18"]),
        (d(7, 3), d(7, 4), "Independence Day", ["itoo", "colossus"]),
        (labor - dt.timedelta(days=2), labor, "Labor Day weekend", ["america"]),
        (d(10, 24), d(10, 31), "Halloween week", ["alone", "dreamwithin", "raven"]),
        (d(10, 28), d(10, 28), "The Statue of Liberty was dedicated on this day in 1886", ["colossus"]),
        (d(11, 1), d(11, 2), "Día de los Muertos", ["death"]),
        (d(11, 10), d(11, 11), "Veterans Day", ["flanders"]),
        (thanks - dt.timedelta(days=2), thanks, "Thanksgiving", ["river"]),
        (d(12, 20), d(12, 26), "Midwinter and the holidays", ["midwinter"]),
        (d(12, 31), d(12, 31), "New Year's Eve", ["langsyne"]),
    ]


SEASONS = {
    "spring": ["gold", "daffodils", "pied", "softrains"],
    "summer": ["sonnet18", "innisfree", "astronomer", "ozymandias"],
    "autumn": ["autumn", "goldengrove", "road", "rainyday"],
    "winter": ["woods", "dust", "fireice", "hope"],
}


def _season(day):
    md = (day.month, day.day)
    if (3, 20) <= md < (6, 21):
        return "spring"
    if (6, 21) <= md < (9, 22):
        return "summer"
    if (9, 22) <= md < (12, 21):
        return "autumn"
    return "winter"


def _weather(today, season):
    """Poem keys and a reason from today's forecast, or None."""
    if not today:
        return None
    code, hi = today.get("code") or 0, today.get("hi") or 60
    wind = max(today.get("wind") or 0, (today.get("gust") or 0) * 0.6)
    if code in (71, 73, 75, 77, 85, 86) or (today.get("snow_in") or 0) > 0.1:
        return ["woods", "dust"], "Snow in the forecast"
    if code in (45, 48):
        return ["fog"], "Fog this morning"
    if code >= 95 or wind >= 25:
        return ["wind", "hope"], "A windy, stormy day"
    if code >= 51 and (today.get("rain_in") or 0) >= 0.05:
        return (["softrains", "rain"] if season == "spring" else ["rainyday", "wheelbarrow", "rain"]), "Rain in the forecast"
    if hi >= 90:
        return ["ozymandias"], "A scorcher"
    return None


def poem_of_the_day(day, today_forecast=None):
    # An occasion's poems count down to its day, one per day with the main one on the day itself,
    # so a week-long window never shows the same poem twice. Other days follow the weather and season.
    # A month-long occasion gets every other day.
    near = lambda o: (o[1] - day).days < len(o[3])
    hits = [o for o in _occasions(day) if o[0] <= day <= o[1] and (near(o) or ((o[1] - o[0]).days >= 14 and day.toordinal() % 2 == 0))]
    if hits:
        start, end, why, keys = min(hits, key=lambda o: (o[1] - o[0]).days)
        key = keys[len(keys) - 1 - (end - day).days] if near((start, end, why, keys)) else keys[day.toordinal() // 2 % len(keys)]
    else:
        season = _season(day)
        weather = _weather(today_forecast, season)
        keys, why = weather or (SEASONS[season], f"It's {season}")
        key = keys[day.toordinal() % len(keys)]
    title, poet, year, text, excerpt = POEMS[key]
    return {"title": title, "poet": poet, "year": year, "text": text, "excerpt": excerpt, "why": why,
            "url": "https://duckduckgo.com/?" + urllib.parse.urlencode({"q": f"! poetryfoundation {title} {poet}"})}
