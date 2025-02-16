# How This Repo Is Made (All The Details You Didn't Care About)

This repository is my latest and hopefully final attempt to figure out a way to open source whatever configurations for assistants that I can. For the few people who starred this repository and then saw it magically disappear, it probably has to do with me deleting and recreating my first couple of failed attempts at indexing these configurations. 

This format will be my "it ain't broken and I'm not fixing it" attempt at collecting and sharing these. Creating these configurations is a lot more fun than figuring out how to write indexing scripts. 

I'm hopeful that as platforms for multi-agent orchrestration continue to evolve we'll arrive at greater standardisation for how to share templates and configs like these. But for the moment rather than root my library to any one platform's unique method, I've chosen an intermediate netural `YAML` method.

For my own later reference, and for anyone who cares, here is how it's constructed:

## Open Web UI Export

After I've had a bit of time to add descriptions and tighten up the system prompts, I export the models from Open Web UI. While its agent orchestration and RAG performance mightn't be as good as dedicated agent platforms, it's a tool that I'm very fond of. True to its name, some truly great UI (a scarce commodity sometimes!)

![alt text](screenshots/1.png)

Unfortunately, the one by one export functionality currently reveals private user information. I might  try to script around that in future, but at the moment I've chosen the bulk export and differential sync approach. 

For anyone using it who hasn't discovered this yet: there's a useful export tool right at the bottom of your 'models' list. This gets you one big `JSON` with all your models in one go.

### The hard part

To get from `JSON` to `YAML` which I prefer for sharing the individual configs:

The JSON is run through a data formatting/pipeline script that took quite a lot of work to put together (happy to share!)

It isolates several parameters and ignores others, then creates 1 YAML per config.

Finally, to avoid sharing personal configurations, I have a basic filter built into it. Then I take a look 

### This repo


Having tried a couple of different approaches to sharing this Assistant library, I've truly grown tired of organizing the same configurations into folders. 

I had some fun on the day I'm writing this, exploring some of the first agentic operating agents that run on Linux. But it was also revealing as to how doing what seems like a fairly simple job of categorization is actually quite complicated. 

Sonnet created a script with a cloud LLM that I had high hopes for but which ended up doing only a very rudimentary job at sorting the configurations into topic based folders. 

Finally, the same script that does the organization attempts to populate new configurations from an export folder from the first script, which may or may not work. 

And that's how I made my assistant library!