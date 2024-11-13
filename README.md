# 987

Just like 2048, but with fibonacci numbers!

Deployed on https://nineeightseven-cyan-star.staging.reflexcorp.run/

## Stack

Frontend and backend built with [reflex](https://reflex.dev). Animations are provided by [reflex-motion](https://github.com/Alek99/reflex-motion.git) which wraps [Motion](https://motion.dev/). Swipe gestures are provided by [reflex-swipe](https://github.com/adhami3310/reflex-swipe.git) which wraps [react-swipeable](https://commerce.nearform.com/open-source/react-swipeable).

## Known Issues

Animations sometimes lag, refreshing should fix the issue.

## Statistical Analysis

Since consequent numbers merge into each other, this game grows half the speed of 2048. To illustrate this, imagine what would be required to get 2048, we need 1024 to merge with another 1024, as such we need to create 1024 that is the result of merging two 512. As such, we need 1024, 512, 256, 128, 64, 32, 16, 8, 4, 2, and one additional 2 to make 2048, for a total of 11 blocks.

However, in 987, we can have 1 and 2 merge to become 3, and that can merge with 5, thus we don't actually need 3 to be present, as such, we only need every other value in the sequenece, essentially doubling how far we can go in the sequence.

It's also easier in nature, as failing the game requries having many of the same value, or two values of more than two apart to be all around the board. As such, this is a difficult criteria to reach compared to 2048.

## Simple Solver

The code contains a simple search to find the best move (although disabled by default). Through a simple run we got it to achieve a score of 66,666. You can most likely build something better.
