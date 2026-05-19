## Week 5

1. What you have achieved so far

I have completed the eBay collection script using eBay's publically available API. I have created my database using SQLAlchemy and SQLite. I have created a general collect script that will run the collections from all the different sites. I have created some tests using pytest to verify everything is working as expected.

2. What you are happy with, from your project work so far

I am happy that my database is working correctly. My collect script seems to be working as well.

3. What you are struggling with, or what challenges you are facing next 

My eBay developer's account got flagged and they are rejecting me from accessing my account. I submitted a request to fix this but I am stalled on the eBay front as I cannot access the API right now. I created an account and am working with ScraperAPI to get data from Grailed. Grailed and especially Depop, Vinted, and The RealReal are heavily bot protected so I am trying to figure out a way around that. I need to figure out the details of what data I am going to store in my database once I get more data from the sites. I need to work on the data pipeline as well.

4. Anything else you’d specifically like the course staff to focus on in giving you feedback or advice

No, just the problems listed in question 3. Progress has been slow because of the issue with eBay and midterms. I will have to work a lot on the project this week.


## Week 7
1. What you have achieved so far

Since week 5, I have completed the data collection pipeline and implemented the core trend detection algorithm. On the collection side, I got Grailed working by using their Algolia search API to pull listing data directly without scraping. For Depop I used ScraperAPI with JavaScript rendering to fetch and parse search result pages with BeautifulSoup. I also significantly expanded the database schema. Collection is now scheduled via cron to run every 12 hours. On the analysis side, I built a keyword extraction pipeline using NLTK that tokenizes listing titles, combines like tokens, filters out garment type words, colors, and listing noise, and preserves multi-word fashion terms like "single stitch" as single tokens. On top of that I implemented a momentum scoring algorithm that computes a trend score for each keyword by comparing its normalized frequency in the latest collection window against a Laplace-smoothed rolling baseline of all prior windows, with a secondary signal from Grailed's engagement heat scores.

2. What you are happy with, from your project work so far

I am happy with the Grailed and Depop collection working. I am also happy with the keyword extraction and filtering with NLTK as that was a big challenge from the raw data pulled from the websites. I am happy with the current momentum scores I have developed but am unsure with how accurate it is in actually detecting trends. This is something I will have to try and verify going forward.

3. What you are struggling with, or what challenges you are facing next

One challenge I am facing is I have maxed out my free credits availible with ScraperAPI so I am limited on the new data I am collecting. I previously talked about an issue with my eBay developer account and the new update is that they denied my appeal so it seems for the forseeable future I will not be able to implement the eBay collection. So my current data stream is confined to only Grailed. Maybe I should implement another website collection. I am also unsure of how to verify that my trends I identified as picking up momentum are actually reflective of real trends in the second hand fashion world.

What I need to work on next is also building a UI for my application.

4. Anything else you’d specifically like the course staff to focus on in giving you feedback or advice

Nothing else specific, just my concerns and challenges in question 3.