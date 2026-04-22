### Prompt:
I am into fashion, menswear, and analyzing fashion trends and I like to shop for clothes online. People in the fashion community are insufferable about being early to new trends. I would like to make a web app that scrapes through secondhand clothing sites to collect listing data over time and applies trend detection analysis to identify styles, items, and keywords that are gaining momentum before they hit the mainstream.

### Execution Plan:
By Week 5: 
- Select a scraper API and confirm they can reliably work on my target sites. I'm going to look into sites like Grailed, Depop, Ebay, Vinted, The RealReal.
- Design and build the data pipeline. I'll write a scheduled collection script that queries each platform for new listings in target categories and stores it in a database. This way I have multiple time windows of data to analyze to detect trends.
- Explore the data initially and see if there is enough to support trend detection.

By Week 7:
- Implement the trend detection algorithm. I'll do this by computing a "momentum score" for keywords and item attributes by comparing their frequency and engagement rate in the most recent time window against a rolling baseline. Items/keywords scores that are accelerating faster than the baseline can be flagged as emerging trend. 
- Build keyword extraction. Remove all the noise on item listings and just use basic NLP to extract keywords and normalyze synonyms.
- Build the UI.

By Final Due Date:
- Add filtering by catagories. (If time permits)
- Evaluate trend detection quality/accuracy.
- Film final video.