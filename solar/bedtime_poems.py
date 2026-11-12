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
    ("Leisure", "W. H. Davies", 1911, """What is this life if, full of care,
We have no time to stand and stare?

No time to stand beneath the boughs
And stare as long as sheep or cows.

No time to see, when woods we pass,
Where squirrels hide their nuts in grass.

No time to see, in broad daylight,
Streams full of stars, like skies at night.

No time to turn at Beauty's glance,
And watch her feet, how they can dance.

No time to wait till her mouth can
Enrich that smile her eyes began.

A poor life this if, full of care,
We have no time to stand and stare."""),
    ("Dust of Snow", "Robert Frost", 1923, """The way a crow
Shook down on me
The dust of snow
From a hemlock tree

Has given my heart
A change of mood
And saved some part
Of a day I had rued."""),
    ("The Pasture", "Robert Frost", 1913, """I'm going out to clean the pasture spring;
I'll only stop to rake the leaves away
(And wait to watch the water clear, I may):
I sha'n't be gone long.—You come too.

I'm going out to fetch the little calf
That's standing by the mother. It's so young,
It totters when she licks it with her tongue.
I sha'n't be gone long.—You come too."""),
    ("Good Hours", "Robert Frost", 1915, """I had for my winter evening walk—
No one at all with whom to talk,
But I had the cottages in a row
Up to their shining eyes in snow.

And I thought I had the folk within:
I had the sound of a violin;
I had a glimpse through curtain laces
Of youthful forms and youthful faces.

I had such company outward bound.
I went till there were no cottages found.
I turned and repented, but coming back
I saw no window but that was black.

Over the snow my creaking feet
Disturbed the slumbering village street
Like profanation, by your leave,
At ten o'clock of a winter eve."""),
    ("Boats Sail on the Rivers", "Christina Rossetti", 1872, """Boats sail on the rivers,
And ships sail on the seas;
But clouds that sail across the sky
Are prettier far than these.

There are bridges on the rivers,
As pretty as you please;
But the bow that bridges heaven,
And overtops the trees,
And builds a road from earth to sky,
Is prettier far than these."""),
    ("Is the Moon Tired?", "Christina Rossetti", 1872, """Is the moon tired? she looks so pale
Within her misty veil:
She scales the sky from east to west,
And takes no rest.

Before the coming of the night
The moon shows papery white;
Before the dawning of the day
She fades away."""),
    ("My Shadow", "Robert Louis Stevenson", 1885, """I have a little shadow that goes in and out with me,
And what can be the use of him is more than I can see.
He is very, very like me from the heels up to the head;
And I see him jump before me, when I jump into my bed.

The funniest thing about him is the way he likes to grow—
Not at all like proper children, which is always very slow;
For he sometimes shoots up taller like an india-rubber ball,
And he sometimes gets so little that there's none of him at all.

He hasn't got a notion of how children ought to play,
And can only make a fool of me in every sort of way.
He stays so close beside me, he's a coward you can see;
I'd think shame to stick to nursie as that shadow sticks to me!

One morning, very early, before the sun was up,
I rose and found the shining dew on every buttercup;
But my lazy little shadow, like an arrant sleepy-head,
Had stayed at home behind me and was fast asleep in bed."""),
    ("Where Go the Boats?", "Robert Louis Stevenson", 1885, """Dark brown is the river,
Golden is the sand.
It flows along for ever,
With trees on either hand.

Green leaves a-floating,
Castles of the foam,
Boats of mine a-boating—
Where will all come home?

On goes the river
And out past the mill,
Away down the valley,
Away down the hill.

Away down the river,
A hundred miles or more,
Other little children
Shall bring my boats ashore."""),
    ("Winter-Time", "Robert Louis Stevenson", 1885, """Late lies the wintry sun a-bed,
A frosty, fiery sleepy-head;
Blinks but an hour or two; and then,
A blood-red orange, sets again.

Before the stars have left the skies,
At morning in the dark I rise;
And shivering in my nakedness,
By the cold candle, bathe and dress.

Close by the jolly fire I sit
To warm my frozen bones a bit;
Or with a reindeer-sled, explore
The colder countries round the door.

When to go out, my nurse doth wrap
Me in my comforter and cap;
The cold wind burns my face, and blows
Its frosty pepper up my nose.

Black are my steps on silver sod;
Thick blows my frosty breath abroad;
And tree and house, and hill and lake,
Are frosted like a wedding-cake."""),
    ("Now Sleeps the Crimson Petal", "Alfred, Lord Tennyson", 1847, """Now sleeps the crimson petal, now the white;
Nor waves the cypress in the palace walk;
Nor winks the gold fin in the porphyry font:
The fire-fly wakens: waken thou with me.

Now droops the milk-white peacock like a ghost,
And like a ghost she glimmers on to me.

Now lies the Earth all Danaë to the stars,
And all thy heart lies open unto me.

Now slides the silent meteor on, and leaves
A shining furrow, as thy thoughts in me.

Now folds the lily all her sweetness up,
And slips into the bosom of the lake:
So fold thyself, my dearest, thou, and slip
Into my bosom and be lost in me."""),
    ("I Never Saw a Moor", "Emily Dickinson", 1890, """I never saw a moor,
I never saw the sea;
Yet know I how the heather looks,
And what a wave must be.

I never spoke with God,
Nor visited in heaven;
Yet certain am I of the spot
As if the chart were given."""),
    ("Barter", "Sara Teasdale", 1917, """Life has loveliness to sell,
All beautiful and splendid things,
Blue waves whitened on a cliff,
Soaring fire that sways and sings,
And children's faces looking up
Holding wonder like a cup.

Life has loveliness to sell,
Music like a curve of gold,
Scent of pine trees in the rain,
Eyes that love you, arms that hold,
And for your spirit's still delight,
Holy thoughts that star the night.

Spend all you have for loveliness,
Buy it and never count the cost;
For one white singing hour of peace
Count many a year of strife well lost,
And for a breath of ecstasy
Give all you have been, or could be."""),
    ("February Twilight", "Sara Teasdale", 1926, """I stood beside a hill
Smooth with new-laid snow,
A single star looked out
From the cold evening glow.

There was no other creature
That saw what I could see—
I stood and watched the evening star
As long as it watched me."""),
    ("The Song of Wandering Aengus", "W. B. Yeats", 1899, """I went out to the hazel wood,
Because a fire was in my head,
And cut and peeled a hazel wand,
And hooked a berry to a thread;
And when white moths were on the wing,
And moth-like stars were flickering out,
I dropped the berry in a stream
And caught a little silver trout.

When I had laid it on the floor
I went to blow the fire a-flame,
But something rustled on the floor,
And someone called me by my name:
It had become a glimmering girl
With apple blossom in her hair
Who called me by my name and ran
And faded through the brightening air.

Though I am old with wandering
Through hollow lands and hilly lands,
I will find out where she has gone,
And kiss her lips and take her hands;
And walk among long dappled grass,
And pluck till time and times are done,
The silver apples of the moon,
The golden apples of the sun."""),
    ("Nod", "Walter de la Mare", 1912, """Softly along the road of evening,
In a twilight dim with rose,
Wrinkled with age, and drenched with dew,
Old Nod, the shepherd, goes.

His drowsy flock streams on before him,
Their fleeces charged with gold,
To where the sun's last beam leans low
On Nod the shepherd's fold.

The hedge is quick and green with briar,
From their sand the conies creep;
And all the birds that fly in heaven
Flock singing home to sleep.

His lambs outnumber a noon's roses,
Yet, when night's shadows fall,
His blind old sheep-dog, Slumber-soon,
Misses not one of all.

His are the quiet steeps of dreamland,
The waters of no-more-pain;
His ram's bell rings 'neath an arch of stars,
"Rest, rest, and rest again.\""""),
    ("Hymn to Diana", "Ben Jonson", 1600, """Queen and huntress, chaste and fair,
Now the sun is laid to sleep,
Seated in thy silver chair,
State in wonted manner keep:
Hesperus entreats thy light,
Goddess excellently bright.

Earth, let not thy envious shade
Dare itself to interpose;
Cynthia's shining orb was made
Heaven to clear when day did close:
Bless us then with wishèd sight,
Goddess excellently bright.

Lay thy bow of pearl apart,
And thy crystal-shining quiver;
Give unto the flying hart
Space to breathe, how short soever:
Thou that mak'st a day of night,
Goddess excellently bright."""),
    ("Under the Greenwood Tree", "William Shakespeare", 1623, """Under the greenwood tree
Who loves to lie with me,
And turn his merry note
Unto the sweet bird's throat,
Come hither, come hither, come hither:
Here shall he see
No enemy
But winter and rough weather.

Who doth ambition shun,
And loves to live i' the sun,
Seeking the food he eats,
And pleased with what he gets,
Come hither, come hither, come hither:
Here shall he see
No enemy
But winter and rough weather."""),
]

# Poems that only suit part of the year.
SEASON = {"Bed in Summer": (5, 8), "Stopping by Woods on a Snowy Evening": (11, 2),
          "I Wandered Lonely as a Cloud": (3, 6), "Dust of Snow": (12, 3),
          "Good Hours": (11, 2), "Winter-Time": (12, 2), "February Twilight": (1, 3),
          "The Pasture": (3, 6)}


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
