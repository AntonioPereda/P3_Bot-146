# P3_Bot-146

Updated protection_plan
* updated logic for strong allies within range sending help
    * for strongest within range, strongest contributes more heavily to help
    * for all others within range not under attack, contribution is lesser compared to strongest

* updated logic for case when no allies within range based on estimated prediction 
    * if esimated to lose
        * if sending help from global strongest ally helps recapture/survival, send help
        * if FUBAR, planet "self destructs" and disperses itself amongst fellow allies under attack
    * if estimated to survive anyways, do nothing

***COULDNT TEST, ON MAC AND python3 run.py ISNT WORKING FOR SOME REASON