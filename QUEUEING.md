QUEUING AND VOTING, clearly stated
========================================

The queue you see in Prosecco is only half the story; the calculation of where a newly-chosen song goes into the queue is the other half, invisible, UNTIL NOW.

The order of when things play is determined by the time at which they were added, with the additional of a few penalties. Let's call the beginning of the workday time 0 (in reality we use the number of seconds since January 1, 1970). The penalty calculation in minutes is the length of all songs the user has in the queue currently, plus two raised to the power of the number of items the user adding a new song already has in the queue. If a song in the queue has any words in the title that overlap with the title of the song being queued **AND** the queue is more than half such songs, then those songs count twice for the exponential penalty.

As an example, users Alice, Bob, and Carol are all listening to Prosecco. At time 0, Alice adds two seven minute songs to an empty queue. Five minutes later, while Alice's first long jam is playing, Bob adds two songs, then Carol adds three. Carol's third song and Bob's second song both have the word 'love' in the title. Alice's first song (7 minutes long) gets a penalty of 0 minutes (0 squared), and her second song gets a penalty of 9 minutes (7 + 2 to the first power). The queue once Alice's first song starts playing is:

1. Alice2 - 9 minutes

After five minutes have passed, Bob's first song (3 minutes long) enters the queue with time 5 minutes, and no penalty; and his second song with a 5 minute penalty (3 + 2 to the first power). Carol's first (4 minutes long) and second songs have the similar penalties (0 and 4 + 2 to the first power) respectively; the third one has a 5 minute offset, plus an 8 minute penalty (2 cubed) due to the keyword overlap, 

1. Bob1 - 5 minutes
1. Carol1 - 5 minutes
1. Alice2 - 9 minutes
1. Bob2 - 10 minutes
1. Carol2 - 11 minutes
1. Carol3 - 14 minutes