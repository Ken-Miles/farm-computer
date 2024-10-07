

import datetime
import logging
import re
import time
from typing import Optional
import urllib.parse

import aiohttp
from bs4 import BeautifulSoup
import bs4
import discord
from discord import app_commands
from discord.ext import commands, tasks

from src.cache import Cache
from src.config import CLEAR_CACHE_HOURS
from src.embed import EmbedBuilder
from src.emotes import getQualityFromPath, identify
from utils import (
    BotU,
    CogU,
    ContextU,
    Cooldown,
    GUILDS,
    generic_autocomplete,
    logger,
    logger_computer,
)

allpages = []

async def wiki_autocomplete(interaction: discord.Interaction, current: str):
    global allpages

    return await generic_autocomplete(current, allpages, interaction=interaction)


class CommandsCog(CogU, name='Farm Computer'):
    prevs: list = []

    def __init__(self, bot: BotU):
        self.cache = Cache(logger, bot)

        self.infloop.start()

        self.session = aiohttp.ClientSession()
        #self.cache.set_ttl(60 * 60 * 24)
        #self.cache.set_max_size(1000)


    @commands.hybrid_command(name="wiki", description = "Search the Stardew Valley Wiki for a specific page.")#guild=MAIN_SERVER)
    @Cooldown(1,5,commands.BucketType.user)
    @app_commands.autocomplete(query=wiki_autocomplete)
    @app_commands.describe(query="What you want to search the Stardew Valley wiki for.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def wiki(self, ctx: ContextU, *, query: str):
        eph = False
        if ctx.guild: 
            eph = ctx.guild.id not in GUILDS

        await ctx.defer()

        start = time.time()

        if ctx.interaction is None and eph:
            mention = await self.bot.get_command_mention('wiki')
            return await ctx.reply(f"You can only use the text version of this command in DMs. Use {mention} instead.",delete_after=5)

        proper_query = query
        if proper_query not in allpages:
            for x in allpages:
                if x.lower().strip() == query.lower().strip():
                    proper_query = x
                    break
        emb = await self.search(proper_query.replace(" ","_").replace("'","%27"),cache=self.cache)
        await ctx.reply(embed=emb)
        end = time.time()
        logger_computer.info(f"Looked up {str(emb.title)[:str(emb.title).find('-')-1]} for {ctx.author} in {end-start} seconds.")

    async def getallpages(self, sites: list=[], prev=None, first_iteration: bool=True):
        print('running')
        r = None
        if prev in self.prevs: return None
        
        if first_iteration:
            r = await self.session.get('https://stardewvalleywiki.com/Special:AllPages?from=&to=z&namespace=0&hideredirects=1')
        else:
            r = await self.session.get(prev)
        
        print('responded')

        r = await r.text()

        if prev:
            print("more data after this")
        elif first_iteration:
            print("first iteration")
        else:
            print("reached last page")

        b = BeautifulSoup(r, 'html.parser')


        for found in b.find("ul", {"class": "mw-allpages-chunk"}).find_all("li"):
            sites.append(found.find("a").get("href"))

        for next in b.find_all('a',{"title": "Special:AllPages"}):
            if "Next page" in next.text:    
                r = await self.getallpages(sites, "https://stardewvalleywiki.com"+next.get("href"), first_iteration=False)  
                self.prevs.append("https://stardewvalleywiki.com"+next.get("href"))  
        returnv = []
        for site in sites:
            returnv.append(str(site.replace("%27","'").replace("%20"," ").replace('_'," "))[1:])
        return returnv

    @commands.Cog.listener()
    async def on_ready(self):
        global allpages
        allpages = await self.getallpages()
        self.prevs.clear()

    @tasks.loop(time=[datetime.time(hour=x, minute=0) for x in range(24)])
    async def infloop(self):
        global allpages
        allpages = await self.getallpages()
        self.prevs.clear()
        if CLEAR_CACHE_HOURS <= 0:
            CLEAR_CACHE_HOURS = 5
        else:
            CLEAR_CACHE_HOURS -= 1
        logger.info(f"Clearing cache in {CLEAR_CACHE_HOURS} hours")


    async def search(
        self, query: str, _logger: Optional[logging.Logger] = None, cache=None
    ) -> discord.Embed:
        if not self.logger:
            self.logger = _logger

        start_time = time.time()

        if isinstance(query, list) or isinstance(query, tuple):
            query = " ".join(query)
        encoded = query.replace(" ", "+")

        r = None
        status = None
        full_href = None

        try:
            url = f"https://stardewvalleywiki.com/{query}"
            r = await self._get(url)
            if r.status > 350:
                # print(r.status)
                raise Exception()
            status = r.status
            full_href = str(r._real_url)
            soup = bs4.BeautifulSoup(await r.text(), "html.parser")
        except Exception:
            # print(r.status)
            url = f"https://stardewvalleywiki.com/mediawiki/index.php?search={encoded}"

            res = await self._get(url)

            soup = bs4.BeautifulSoup(await res.text(), "html.parser")

            # logger.info(f'Got status code: {res.status_code}')
            # logger.info(f'Got url: {res.url}')

            redir = False
            if res.status in [301, 302, 304]:
                try:
                    redir = soup.find_all("meta", {"property": "og:url"})[0]["content"]
                except Exception:
                    pass

            if redir:
                # return parse(redir)
                return await cache.get(redir)

            for li in soup.find_all("li", {"class": "mw-search-result"}):
                href = li.find_all("a")[0]["href"]
                full_href = f"https://stardewvalleywiki.com{href}"

            if full_href != url and full_href != urllib.parse.urlparse(url).path:
                r = await self._get(full_href)
                status = r.status

        if status == 200:
            # return parse(full_href)
            return await cache.get(full_href)
        elif status in [301, 302, 304]:
            redirected_link = r.url
            # return parse(redirected_link)
            return await cache.get(redirected_link)

        # return parse(res.url)
        if soup.find("p", {"class": "mw-search-createlink"}):
            return help().build()
        resp = await cache.get(str(res.url))

        logger.info(f"Got response for {query} in {time.time() - start_time} seconds")
        return resp


    async def parse(self, url: str, build: bool=True) -> discord.Embed:
        embed = EmbedBuilder(fields=[], color=discord.Color.orange())

        logger.info(f"Parsing url: {url}")

        if (
            "https://stardewvalleywiki.com/Special:Search" in url
            or "https://stardewvalleywiki.com/mediawiki/index.php?search=" in url
            or not url
        ):

            return help().build() if build else help()

        html = await (await self._get(url)).text()
        soup = bs4.BeautifulSoup(html, "html.parser")

        # find the first <img> that does NOT have a srcset attr

        main_logo_url = "https://stardewvalleywiki.com/mediawiki/images/6/68/Main_Logo.png"

        try:

            embed.thumbnail = (
                "https://stardewvalleywiki.com"
                + soup.find_all("img", {"srcset": False})[0]["src"]
            )
            if (
                embed.thumbnail
                == "https://stardewvalleywiki.com/mediawiki/resources/assets/licenses/cc-by-nc-sa.png"
            ):
                embed.image = main_logo_url
                embed.thumbnail = None

        except Exception:
            embed.image = main_logo_url

        pagename = soup.find_all("h1", {"id": "firstHeading"})[0].text
        embed.title = pagename + " - Stardew Valley Wiki"
        embed.url = url

        # find all id=infoboxtable > tr that have a infoboxsection and infoboxdetail

        infobox = soup.find_all("table", {"id": "infoboxtable"})

        # logger.info(f'Found infoboxtable: {infobox}')

        if infobox:
            infobox = infobox[0]

            trs = infobox.find_all("tr")

            for tr in trs:
                # logger.info(f'Found tr: {tr}')
                # try:
                if tr.find_all(
                    "table", {"style": "width:101%;"}
                ):  # or tr.find_all('div', {'class': 'parent'}):
                    break
                section = tr.find_all("td", {"id": "infoboxsection"})
                detail = tr.find_all("td", {"id": "infoboxdetail"})

                if section:
                    section = section[0].text
                    # logger.info(f'Found section: {section}')

                if detail:
                    detail = detail[0]

                if not section or not detail:
                    continue

                if (table := detail.find_all("table")) and section.strip() != "Sell Price":
                    table = table[0]
                    rows = table.find_all("tr")

                    first_row = rows[0]

                    text = ""
                    for row in rows:
                        do_newline = True
                        if row.find_all("tr"):
                            continue
                        for i, td in enumerate(row.find_all("td")):
                            # logger.info(f'Found td: {td}')

                            if backimages := td.find_all("div", {"class": "backimage"}):

                                # logger.info(f'Found backimage: {backimages}')
                                emoji = identify(
                                    backimages[0].find_all("img")[0]["src"],
                                    pagename,
                                    foreimages=td.find_all("div", {"class": "foreimage"}),
                                )

                                # logger.info(f'Emoji: {emoji}')
                                text += f"{emoji} "
                            inner = td.text.strip()
                            if not inner:
                                continue
                            elif (
                                td.has_attr("style")
                                and "vertical-align: bottom;" in td["style"]
                            ):
                                # logger.info(f'Found td with style: {td["style"]}')
                                text += f"{inner} "
                            elif not td.children or not td.attrs:
                                # logger.info(f'Found td with no children/attrs')
                                do_newline = False
                                text += f"{inner} "
                            # logger.info(f'Found inner: *{inner}*')

                            # check if the next td has no attrs and no children
                            if i + 1 < len(row.find_all("td")):
                                next_td = row.find_all("td")[i + 1]
                                if not next_td.attrs and not next_td.children:
                                    do_newline = False
                            elif row.parent != first_row.parent:
                                do_newline = False

                        # logger.info(f'Found row: {row}')

                        if do_newline:
                            text += "\n"

                    detail = text

                elif spans := detail.find_all("span", {"class": "no-wrap"}):
                    detail = spans[0].text
                elif spans := detail.find_all("span", {"style": "display: none;"}):
                    # logger.info(f'Found span: {spans}')
                    detail = detail.text.replace(spans[0].text, "")

                elif spans := detail.find_all("span", {"class": "nametemplate"}):
                    items = []
                    for span in spans:
                        items.append(span.text)
                    detail = ", ".join(items)

                elif p_tags := detail.find_all(
                    "p", {"class": lambda x: x != "mw-empty-elt"}
                ):
                    items = []
                    for p in p_tags:
                        items.append(p.text)

                    detail = ", ".join(items)
                elif [
                    x for x in detail.find_all("img") if x["alt"].endswith(" Quality.png")
                ]:
                    # getinnerhtml of the detail

                    # replace all LOOSE TEXT in the detail with a <loose> tag
                    for child in detail.children:
                        if isinstance(child, bs4.element.NavigableString):
                            # child.replace_with(f'<loose>{child}</loose>') will escape the <>
                            # so we have to do this instead
                            child.wrap(soup.new_tag("span"))

                    # logger.info(f'Found child: {str(detail.children)}')
                    # extract the img/span pairs
                    # the html is like this:
                    # text, img | text, img | text, img | text
                    pairs = []
                    skip = False
                    for i, child in enumerate(detail.children):
                        if skip:
                            skip = False
                            continue
                        if isinstance(child, bs4.element.Tag):
                            # check if its an img, if it is, get the next child, otherwise set the img inthe aay to none
                            if child.name == "img":
                                img = child.attrs["src"]
                                text = detail.contents[i + 1].text

                                # for some reason it has weird escaped unicode
                                text = "".join(
                                    [i if ord(i) < 128 else " " for i in text]
                                ).strip()

                                pairs.append((text, img))
                                skip = True
                            else:
                                pairs.append((child.text, None))

                    # logger.info(f'Found pairs: {str(pairs)}')

                    detail = ""
                    for pair in pairs:
                        if pair[1]:
                            detail += f"{getQualityFromPath(pair[1])} {pair[0]} "
                        else:
                            detail += f"{pair[0]}"

                else:
                    detail = detail.text

                embed.fields.append({"name": section, "value": detail, "inline": False})
                # except Exception as e:
                #     logger.error(f'Error failed to parse tr: {e} on line {e.__traceback__.tb_lineno}')
                #     # throw the error
                #     # raise e
                #     pass
        else:
            body = soup.find_all("div", {"class": "mw-parser-output"})[0]
            #  get the first two <p> tags
            for p in body.find_all("p")[:2]:
                embed.description += cleanSellPrice(p.text) + "\n\n"
        # logger.info(f'Got embed: {embed}')
        # return embed.build()
        return embed.build() if build else embed

def cleanSellPrice(price: str) -> str:
    regex = r'data-sort-value="[a-zA-Z0-9-_ ]+"'
    return re.sub(regex, "", price)


async def setup(bot: BotU):
    cog = CommandsCog(bot)
    await bot.add_cog(cog)

