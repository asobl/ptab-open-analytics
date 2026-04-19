# Medium Article Draft -- PTAB Open Analytics

**Title:** I Built a Free Tool to Understand Patent Challenges. Here's What the Data Taught Me.

**Subtitle:** A non-lawyer founder's exploration of PTAB, the federal board that can cancel any patent in America.

---

I am not a patent attorney. I am a tech founder who spent several years deep in patent strategy because the stakes were real, and I found the data I needed was public but the tools to make sense of it cost $30,000 a year.

So I built my own. And in the process I went deep on a corner of the legal world that most people outside of IP law have never heard of, even though it has shaped some of the biggest technology battles of the last decade.

This is what I learned.

---

## First, some history.

For most of American history, if you wanted to challenge a patent, you had to go to federal court. That meant millions of dollars in litigation, years of discovery, and outcomes that were hard to predict. The system strongly favored whoever held the patent, because the cost of fighting it often exceeded the cost of just settling.

The 2000s changed this. Patent assertion entities, companies that buy up patents and sue operating businesses without ever building a product, exploded. By 2011, they accounted for the majority of patent lawsuits in the United States. Small companies were being hit with demand letters they couldn't afford to fight. Large companies were spending hundreds of millions on litigation budgets.

Congress responded with the America Invents Act, signed in 2011, effective September 2012. It created the Patent Trial and Appeal Board, or PTAB. The idea was simple: give companies a faster, cheaper way to challenge patents they believed were invalid, without going through a full federal trial.

The result was anything but simple.

---

## What PTAB actually does.

When a company files an Inter Partes Review petition at PTAB, they are essentially arguing that a patent should never have been granted. The patent was obvious. Prior art already existed. The claims are too broad. A panel of Administrative Patent Judges reviews the petition and decides whether to institute a full review. If they do, the patent owner has to defend it. If the patent doesn't survive, it gets canceled.

The process takes roughly a year from filing to final written decision. It costs a fraction of district court litigation. And the institution rate, historically, has been around 60 to 70 percent.

That number matters. It means that if someone files a serious challenge against your patent, there is roughly a 60 percent chance the review proceeds. And if it proceeds, there is a high probability the patent gets invalidated on at least some claims.

Patent attorneys started calling PTAB the "patent death squad." That phrase was not a compliment.

---

## The cases that defined what PTAB could do.

The Apple and Masimo fight is the clearest modern example of how high the stakes get.

Masimo is a medical device company that pioneered pulse oximetry, the technology that measures blood oxygen levels. When Apple added similar health monitoring to the Apple Watch, Masimo sued. Apple responded by filing dozens of IPR challenges against Masimo's patents at PTAB. Our data shows 70 filings from Apple against Masimo, one of the highest concentrations in the entire dataset.

The fight spilled over into the International Trade Commission. In late 2023, an ITC judge ruled that Apple Watch infringed Masimo's patents. Apple Watch Series 9 and Ultra 2 were briefly banned from sale in the United States. Apple removed the blood oxygen feature from affected models to get the ban lifted while the legal fight continued.

This is a company with a trillion dollar market cap fighting a $5 billion medical device company over a sensor. PTAB is in the middle of all of it.

The Jawbone story goes the other direction. Jawbone, the wearable company, went bankrupt in 2017. Its patents were acquired by a holding entity called Jawbone Innovations. That entity then filed lawsuits against Fitbit, Apple, and others using those patents. Our data shows Jawbone Innovations as one of the most challenged respondents in the entire PTAB dataset, with 111 proceedings filed against them. Companies that were sued used PTAB to try to kill the patents being asserted.

This is what the concentrated NPE data actually represents. One entity sues dozens of companies. Each company files its own IPR to invalidate the patent. The respondent chart fills up with that one entity's name.

---

## What the data actually shows.

I pulled every PTAB proceeding and decision from the USPTO API since 2012. Here is what stood out.

Institution rates peaked around 2020-2022 at roughly 70-75 percent. In 2025, the data shows a sharp drop to around 28 percent. Something is shifting in how PTAB operates. Policy changes, leadership changes at the USPTO, and a series of director review decisions have been pulling institution rates down. This is one of the most important things for anyone watching this space to understand: PTAB is not static. The odds change.

The top petitioners are exactly who you would expect. Apple with 1,112 filings. Samsung with 934. Google with 580. These companies have dedicated IPR teams. They file challenges as a matter of course when patents threaten their products or when they are sued.

But the win rates vary significantly. Meta wins 87 percent of the challenges they file. Halliburton wins 91 percent. Some companies are dramatically better at this than others, which says something about how seriously they have invested in the process.

The judge panel assigned to a case matters more than most people realize. Among high-volume Administrative Patent Judges, institution rates range from under 50 percent to over 85 percent. This has never been easily visible in one place before.

---

## Why this matters if you are building something.

Most founders I talk to fall into one of two camps. They either ignore patents entirely, or they file patents without thinking about whether those patents could survive a challenge.

The PTAB data reframes the question. A patent is not a permanent asset. It is an asset that someone can challenge, at a relatively low cost, with roughly 60 percent odds of getting a full review. If you are in a market where large incumbents have dedicated IPR teams, your patent portfolio is only as strong as its weakest claim.

The long tail of the PTAB dataset, the thousands of entities that show up once or twice in the respondent data, is almost certainly operating companies and startups getting challenged by specific competitors. The NPEs dominate the top of the chart because one NPE patent can generate dozens of challenges from different defendants. But down the list, it is real companies defending real products.

The 60 percent institution rate applies to everyone equally. A startup facing its first IPR has the same statistical odds as Apple. It just has less firepower to fight back.

---

## The tool is free.

I published everything at asobl.github.io/ptab-open-analytics. The data is pulled directly from the USPTO API. The code is on GitHub. No login, no paywall, updated quarterly.

I am not a patent attorney and nothing here is legal advice. But if you have a patent portfolio and you want to understand what the historical odds look like in your technology area, or who has been filing challenges in your space, this is the baseline.

If you find something interesting in the data, I would genuinely like to hear about it.

---

*Status: draft, not published. Written April 2026.*
*To publish: review facts on Apple/Masimo ITC ruling date, post to medium.com/@adsobol*
