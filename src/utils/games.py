#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Games for the bot'''

#-------------------------------------------------------------------------------

import discord
from discord.ext import commands
from discord.ext.commands import Context
import random
import asyncio


class Games(commands.Cog, name="Games"):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}  # Store active games

    

    @commands.command(name="bingo", description="Play a game of bingo.")
    async def bingo(self, context: Context, *players: discord.Member):
        if not 1 <= len(players):
            embed = discord.Embed(
                title="Bingo",
                description=f"Use `{self.bot.prefix}bingo <@player>...` to start a game of bingo.",
                color=0xBEBEFE,
            )
            print("Game started")
            await context.send(embed=embed)
            return

        game_id = context.guild.id+""+context.channel.id
        if game_id in self.games:
            embed = discord.Embed(
                title="Bingo",
                description=f"A game is already in progress in this server. :slight_frown:",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
            return

        self.games[game_id] = {"channel": context.channel,
                               "players": players,
                               "scores": {}, 
                               "status": "ongoing"
                               }

        for player in self.games[game_id]["players"]:
            chart = await self.create_bingo_chart()
            self.games[game_id]["scores"][player.id] = {"chart": chart, "score": 0}
            embed = discord.Embed(
                title="Bingo",
                description=f"Your Bingo Chart:\n{self.format_bingo_chart(chart)}",
                color=0xBEBEFE,
            )
            print("bingo chart "+self.format_bingo_chart(chart))
            try:
                await player.send(embed=embed)
            except discord.Forbidden:
                embed = discord.Embed(
                    title="Bingo",
                    description=f"Please enable DMs from server members to play bingo.{player.mention} :slight_frown: \n Game cancelled.",
                    color=0xBEBEFE,
                )
                await context.send(embed=embed)
                del self.games[game_id]
                return
            
        embed = discord.Embed(
            title="Bingo",
            description=f"Game started for {', '.join([player.mention for player in self.games[game_id]['players']])}! \nLet's see who gets a bingo first! :slight_smile:",
            color=0xBEBEFE,
        )
        await context.send(embed=embed)

        while self.games[game_id]["status"] == "ongoing":
            for player in self.games[game_id]["players"]:
                await self.play_turn(context, player)

        self.games[game_id]["status"] = "finished"
        embed = discord.Embed(
            title="Bingo",
            description=f"Game finished! \nFinal scores:\n\n:tada: :partying_face: :tada:\n\n{self.get_scores_message(game_id)} \n:tada: :partying_face: :tada:",
            color=0xBEBEFE,
        )
        await context.send(embed=embed)
        del self.games[game_id]
        return

    @commands.command(name="quit", description="Quit the current game.")
    async def quit(self, context: Context):
        game_id = context.guild.id
        if game_id not in self.games:
            embed = discord.Embed(
                title="Bingo",
                description=f"No game is in progress in this server.",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
            return

        if context.author not in self.games[game_id]["players"]:
            embed = discord.Embed(
                title="Bingo",
                description=f"You are not in the game.",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="Bingo",
            description=f"Game has to end :slight_frown:\nFinal scores:\n{self.get_scores_message(game_id)}",
            color=0xBEBEFE,
        )
        await context.send(embed=embed)
        del self.games[game_id]


    async def create_bingo_chart(self):
        numbers = list(range(1, 26))
        random.shuffle(numbers)
        return [numbers[i:i + 5] for i in range(0, 25, 5)]

    async def play_turn(self, context: Context, player: discord.Member):
        game_id = context.guild.id+""+context.channel.id
        current_chart = self.games[game_id]["scores"][player.id]["chart"]

        embed = discord.Embed(
            title="Bingo",
            description=f"It's your turn to play! \nYour Bingo Chart:\n{self.format_bingo_chart(current_chart)}",
            color=0xBEBEFE,
        )
        await player.send(embed=embed)

        embed = discord.Embed(
            title="Bingo",
            description=f"{player.mention} turn to play! \nLet's wait for them to call a number.",
            color=0xBEBEFE,
        )
        for p in self.games[game_id]["players"]:
            if p != player:
                await p.send(embed=embed)

        while True:
            try:
                number = await self.get_number_input(player)
                if self.check_valid_number(current_chart, number):
                    break
                else:
                    embed = discord.Embed(
                        title="Bingo",
                        description=f"The number {number} is not in your chart. Please enter a valid number.",
                        color=0xBEBEFE,
                    )
                    await player.send(embed=embed)
            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="Bingo",
                    description=f"You took too long to respond. \nTurn skipped.",
                    color=0xBEBEFE,
                )
                await player.send(embed=embed)
                return
            
        for p in self.games[game_id]["players"]:
            self.games[game_id]["scores"][p.id]["chart"] = self.strike_number(self.games[game_id]["scores"][p.id]["chart"], number)
            if p != player:
                embed = discord.Embed(
                    title="Bingo",
                    description=f"{player.mention} called {number}! {p.mention} \nBingo Chart:\n{self.format_bingo_chart(self.games[game_id]['scores'][p.id]['chart'])}",
                    color=0xBEBEFE,
                )
                await p.send(embed=embed)
            elif p == player:
                embed = discord.Embed(
                    title="Bingo",
                    description=f"You called {number}! \nyour Bingo Chart:\n{self.format_bingo_chart(self.games[game_id]['scores'][p.id]['chart'])}",
                    color=0xBEBEFE,
                )
                await p.send(embed=embed)

        score_updated = False 
        for p in self.games[game_id]["players"]:
            score = self.check_bingo_score(self.games[game_id]["scores"][p.id]["chart"])
            if score > self.games[game_id]["scores"][p.id]["score"]:
                self.games[game_id]["scores"][p.id]["score"] = score
                score_updated = True
                embed = discord.Embed(
                    title="Bingo",
                    description=f"{p.mention} You score is increased to {score}!",
                    color=0xBEBEFE,
                )
                await player.send(embed=embed)

        if score_updated:
            embed = discord.Embed(
                title="Bingo",
                description=f"Updated scores:\n{self.get_scores_message(game_id)} \n :tada:",
                color=0xBEBEFE,
            )
            for p in self.games[game_id]["players"]:
                await p.send(embed=embed)
            await self.games[game_id]["channel"].send(embed=embed)

            winners = self.check_bingo(game_id)
            if winners is not None:
                embed = discord.Embed(
                    title="Bingo",
                    description=f"{', '.join([winner.mention for winner in winners])} got a bingo :clap: ! They won the game! :partying_face: :partying_face:",
                    color=0xBEBEFE,
                )
                await self.games[game_id]["channel"].send(embed=embed)
                for p in self.games[game_id]["players"]:
                    if p not in winners:
                        embed = discord.Embed(
                            title="Bingo",
                            description=f"{', '.join([winner.mention for winner in winners])} got a bingo! Better luck next time :slight_frown:",
                            color=0xBEBEFE,
                        )
                        await p.send(embed=embed)
                    elif p in winners:
                        embed = discord.Embed(
                            title="Bingo",
                            description=f"You won the game! Congratulations :tada:",
                            color=0xBEBEFE,
                        )
                        await p.send(embed=embed)


    async def get_number_input(self, player: discord.Member):
        embed = discord.Embed(
            title="Bingo",
            description=f"Please enter a number present in your chart.",
            color=0xBEBEFE,
        )
        await player.send(embed=embed)
        try:
            msg = await self.bot.wait_for('message', timeout=60.0, check=lambda m: m.author == player)
            return int(msg.content)
        except ValueError:
            embed = discord.Embed(
                title="Bingo",
                description=f"Invalid input. Please enter a valid number.",
                color=0xBEBEFE,
            )
            await player.send(embed=embed)
            return await self.get_number_input(player)

    def format_bingo_chart(self, chart):
        chart_display = str()
        for i, row in enumerate(chart):
            chart_display += "||"
            for j, cell in enumerate(row):
                if cell > 0:
                    chart_display += f" {cell:2} "
                elif cell < 0:
                    chart_display += f"  X "
                chart_display += " " if j < 4 else "||"
            chart_display += "\n" if i < 4 else ""
        return f"```\n{chart_display}```"

    def check_bingo(self, game_id):
        winners = []
        for p in self.games[game_id]["players"]:
            if self.games[game_id]["scores"][p.id]["score"] >= 5:
                winners.append(p)
        if len(winners) > 0:
            self.games[game_id]["status"] = "finished"
            return winners
        if len(winners) == 0:
            return None


    def strike_number(self, chart, number):
        return [[-cell if cell == number else cell for cell in row] for row in chart]

    def check_valid_number(self, chart, number):
        return any(number in row for row in chart)

    def check_bingo_score(self, chart):
        cross_count = 0
        # Check rows
        cross_count += sum(all(cell < 0 for cell in row) for row in chart)
        # Check columns
        cross_count += sum(all(row[i] < 0 for row in chart) for i in range(5))
        # Check diagonals
        cross_count += all(chart[i][i] < 0 for i in range(5))
        cross_count += all(chart[i][4 - i] < 0 for i in range(5))
        return cross_count

    def get_scores_message(self, game_id):
        msg = str()
        score_list = [self.games[game_id]["scores"][p.id]["score"] for p in self.games[game_id]["players"]]
        for p in self.games[game_id]["players"]:
            score = self.games[game_id]["scores"][p.id]["score"]
            msg += f"{p.mention}: ({self.games[game_id]['scores'][p.id]['score']}) :\t"
            if score == 0:
                msg += "**B I N G O**"
            elif score == 1:
                msg += "**~~B~~ I N G O**"
            elif score == 2:
                msg += "**~~B I~~ N G O**"
            elif score == 3:
                msg += "**~~B I N~~ G O**"
            elif score == 4:
                msg += "**~~B I N G~~ O**"
            elif score == 5:
                msg += "**~~B I N G O~~**"
            if score == max(score_list):
                msg += "\t:crown:"
            msg += "\n"
        return msg

async def setup(bot):
    await bot.add_cog(Games(bot))