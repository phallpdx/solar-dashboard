"""Bedtime poems for the evening edition: short, rhymed or steady in metre, about night, water,
weather and rest. Every one is in the public domain. Nothing about war, grief, illness or
sleeplessness, and nothing that needs working out.
"""
import datetime as dt

# (title, poet, year, text)
POEMS = [
    ("She Walks in Beauty", "Lord Byron", 1814, """She walks in beauty, like the night
Of cloudless climes and starry skies;
And all that's best of dark and bright
Meet in her aspect and her eyes:
Thus mellowed to that tender light
Which heaven to gaudy day denies.

One shade the more, one ray the less,
Had half impaired the nameless grace
Which waves in every raven tress,
Or softly lightens o'er her face;
Where thoughts serenely sweet express,
How pure, how dear their dwelling-place.

And on that cheek, and o'er that brow,
So soft, so calm, yet eloquent,
The smiles that win, the tints that glow,
But tell of days in goodness spent,
A mind at peace with all below,
A heart whose love is innocent!"""),
    ("Escape at Bedtime", "Robert Louis Stevenson", 1885, """The lights from the parlour and kitchen shone out
Through the blinds and the windows and bars;
And high overhead and all moving about,
There were thousands of millions of stars.
There ne'er were such thousands of leaves on a tree,
Nor of people in church or the Park,
As the crowds of the stars that looked down upon me,
And that glittered and winked in the dark.

The Dog, and the Plough, and the Hunter, and all,
And the star of the sailor, and Mars,
These shone in the sky, and the pail by the wall
Would be half full of water and stars.
They saw me at last, and they chased me with cries,
And they soon had me packed into bed;
But the glory kept shining and bright in my eyes,
And the stars going round in my head."""),
    ("Sweet and Low", "Alfred, Lord Tennyson", 1850, """Sweet and low, sweet and low,
Wind of the western sea,
Low, low, breathe and blow,
Wind of the western sea!
Over the rolling waters go,
Come from the dying moon, and blow,
Blow him again to me;
While my little one, while my pretty one, sleeps.

Sleep and rest, sleep and rest,
Father will come to thee soon;
Rest, rest, on mother's breast,
Father will come to thee soon;
Father will come to his babe in the nest,
Silver sails all out of the west
Under the silver moon:
Sleep, my little one, sleep, my pretty one, sleep."""),
    ("Stars", "Sara Teasdale", 1920, """Alone in the night
On a dark hill
With pines around me
Spicy and still,

And a heaven full of stars
Over my head,
White and topaz
And misty red;

Myriads with beating
Hearts of fire
That aeons
Cannot vex or tire;

Up the dome of heaven
Like a great hill,
I watch them marching
Stately and still,

And I know that I
Am honored to be
Witness
Of so much majesty."""),
    ("The Lake Isle of Innisfree", "W. B. Yeats", 1890, """I will arise and go now, and go to Innisfree,
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
I hear it in the deep heart's core."""),
    ("Silver", "Walter de la Mare", 1913, """Slowly, silently, now the moon
Walks the night in her silver shoon;
This way, and that, she peers, and sees
Silver fruit upon silver trees;
One by one the casements catch
Her beams beneath the silvery thatch;
Couched in his kennel, like a log,
With paws of silver sleeps the dog;
From their shadowy cote the white breasts peep
Of doves in a silver-feathered sleep;
A harvest mouse goes scampering by,
With silver claws, and silver eye;
And moveless fish in the water gleam,
By silver reeds in a silver stream."""),
    ("The Moon", "Robert Louis Stevenson", 1885, """The moon has a face like the clock in the hall;
She shines on thieves on the garden wall,
On streets and fields and harbour quays,
And birdies asleep in the forks of the trees.

The squalling cat and the squeaking mouse,
The howling dog by the door of the house,
The bat that lies in bed at noon,
All love to be out by the light of the moon.

But all of the things that belong to the day
Cuddle to sleep to be out of her way;
And flowers and children close their eyes
Till up in the morning the sun shall arise."""),
    ("I Wandered Lonely as a Cloud", "William Wordsworth", 1815, """I wandered lonely as a cloud
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
Tossing their heads in sprightly dance.

The waves beside them danced; but they
Out-did the sparkling waves in glee:
A poet could not but be gay,
In such a jocund company:
I gazed and gazed but little thought
What wealth the show to me had brought:

For oft, when on my couch I lie
In vacant or in pensive mood,
They flash upon that inward eye
Which is the bliss of solitude;
And then my heart with pleasure fills,
And dances with the daffodils."""),
    ("The Moon Was but a Chin of Gold", "Emily Dickinson", 1896, """The moon was but a chin of gold
A night or two ago,
And now she turns her perfect face
Upon the world below.

Her forehead is of amplest blond;
Her cheek like beryl stone;
Her eye unto the summer dew
The likest I have known.

Her lips of amber never part;
But what must be the smile
Upon her friend she could bestow
Were such her silver will!

And what a privilege to be
But the remotest star!
For certainly her way might pass
Beside your twinkling door.

Her bonnet is the firmament,
The universe her shoe,
The stars the trinkets at her belt,
Her dimities of blue."""),
    ("He Wishes for the Cloths of Heaven", "W. B. Yeats", 1899, """Had I the heavens' embroidered cloths,
Enwrought with golden and silver light,
The blue and the dim and the dark cloths
Of night and light and the half-light,
I would spread the cloths under your feet:
But I, being poor, have only my dreams;
I have spread my dreams under your feet;
Tread softly because you tread on my dreams."""),
    ("Stopping by Woods on a Snowy Evening", "Robert Frost", 1923, """Whose woods these are I think I know.
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
And miles to go before I sleep."""),
    ("The Owl and the Pussy-Cat", "Edward Lear", 1871, """The Owl and the Pussy-cat went to sea
In a beautiful pea-green boat,
They took some honey, and plenty of money,
Wrapped up in a five-pound note.
The Owl looked up to the stars above,
And sang to a small guitar,
"O lovely Pussy! O Pussy, my love,
What a beautiful Pussy you are,
You are,
You are!
What a beautiful Pussy you are!"

Pussy said to the Owl, "You elegant fowl!
How charmingly sweet you sing!
O let us be married! too long we have tarried:
But what shall we do for a ring?"
They sailed away, for a year and a day,
To the land where the Bong-tree grows,
And there in a wood a Piggy-wig stood
With a ring at the end of his nose,
His nose,
His nose,
With a ring at the end of his nose.

"Dear Pig, are you willing to sell for one shilling
Your ring?" Said the Piggy, "I will."
So they took it away, and were married next day
By the Turkey who lives on the hill.
They dined on mince, and slices of quince,
Which they ate with a runcible spoon;
And hand in hand, on the edge of the sand,
They danced by the light of the moon,
The moon,
The moon,
They danced by the light of the moon."""),
    ("Who Has Seen the Wind?", "Christina Rossetti", 1872, """Who has seen the wind?
Neither I nor you:
But when the leaves hang trembling,
The wind is passing through.

Who has seen the wind?
Neither you nor I:
But when the trees bow down their heads,
The wind is passing by."""),
    ("I'll Tell You How the Sun Rose", "Emily Dickinson", 1890, """I'll tell you how the sun rose,—
A ribbon at a time.
The steeples swam in amethyst,
The news like squirrels ran.

The hills untied their bonnets,
The bobolinks begun.
Then I said softly to myself,
"That must have been the sun!"

But how he set, I know not.
There seemed a purple stile
Which little yellow boys and girls
Were climbing all the while

Till when they reached the other side,
A dominie in gray
Put gently up the evening bars,
And led the flock away."""),
    ("It Is a Beauteous Evening", "William Wordsworth", 1807, """It is a beauteous evening, calm and free,
The holy time is quiet as a Nun
Breathless with adoration; the broad sun
Is sinking down in its tranquillity;
The gentleness of heaven broods o'er the Sea:
Listen! the mighty Being is awake,
And doth with his eternal motion make
A sound like thunder, everlastingly.
Dear Child! dear Girl! that walkest with me here,
If thou appear untouched by solemn thought,
Thy nature is not therefore less divine:
Thou liest in Abraham's bosom all the year;
And worshipp'st at the Temple's inner shrine,
God being with thee when we know it not."""),
    ("Bed in Summer", "Robert Louis Stevenson", 1885, """In winter I get up at night
And dress by yellow candle-light.
In summer, quite the other way,
I have to go to bed by day.

I have to go to bed and see
The birds still hopping on the tree,
Or hear the grown-up people's feet
Still going past me in the street.

And does it not seem hard to you,
When all the sky is clear and blue,
And I should like so much to play,
To have to go to bed by day?"""),
]

# Poems that only suit part of the year.
SEASON = {"Bed in Summer": (5, 8), "Stopping by Woods on a Snowy Evening": (11, 2),
          "I Wandered Lonely as a Cloud": (3, 6)}


def _in_season(title, month):
    if title not in SEASON:
        return True
    a, b = SEASON[title]
    return a <= month <= b if a <= b else month >= a or month <= b


def tonight(night, avoid_title=None):
    """Tonight's poem: walks the pool in a fixed order, one a night, skipping out-of-season
    poems and the one the morning edition printed today."""
    pool = [p for p in POEMS if _in_season(p[0], night.month)]
    start = night.toordinal() % len(pool)
    for k in range(len(pool)):
        p = pool[(start + k) % len(pool)]
        if not avoid_title or p[0].lower() != avoid_title.lower():
            title, poet, year, text = p
            return {"title": title, "poet": poet, "year": year, "text": text}
    return None
