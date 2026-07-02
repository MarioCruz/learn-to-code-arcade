# The cheap computer is getting expensive

### For a lot of kids it was the door in. Now it is closing.

I paid twenty-five dollars for my first Raspberry Pi. I paid attention to what that little computer did for the kids who did not have a maker at home, and that is the part I keep thinking about now.

Here is what twenty-five, thirty-five dollars really bought. It bought a kid permission to break something. It bought a classroom a cart of computers nobody had to guard. It was a way in for a family that could not afford a "real" computer. The Pi was never the fastest thing in the room. It was the one nobody was afraid of, and being cheap was the entire point.

## What broke

Memory prices. DRAM, the working memory a computer needs to run.

The short version is that the big memory makers would rather sell to the data centers building AI machines than to the rest of us. They pointed their factories at the expensive high-bandwidth memory those racks want, and the ordinary DRAM a Raspberry Pi uses got scarce. As of early 2026 the memory those boards use costs about seven times what it did a year earlier. Seven times.

Raspberry Pi passed it along, because what else could they do. A 2GB board went up ten dollars, a 4GB fifteen, an 8GB thirty, and the 16GB Pi 5 sixty. That 16GB Pi 5 launched at a hundred and twenty dollars. It is over three hundred now. Jeff Geerling, who knows this corner better than almost anyone, wrote a post called "DRAM pricing is killing the hobbyist SBC market," and he is right.

There is still a cheap corner. The 1GB Pi 4 is holding at thirty-five dollars, the Pico 2 is five, the Zero 2 W is fifteen. But the Pi you would actually put in front of a kid, the 4GB or 8GB one that runs a browser and an editor without a fight, is not a twenty-five-dollar decision anymore. It did not vanish overnight. It is drifting out of reach, and the kids who could least afford the change are the ones losing the most.

## So what do you put in front of a kid now

Don't skip the Pi. I still love mine. But when the goal is to get a kid started this week, on a budget, without a soldering iron, here is what I would reach for: a four-inch ESP32 touchscreen. About fifteen dollars. A microcontroller, a full color touch screen, and pins to add sensors, all on one board, in a box with a USB-C cable and a stylus.

Is it better than a Raspberry Pi?

No. Not even close. A Pi is a real Linux computer that happens to be small. This is a microcontroller. It will not run a browser or a desktop, and it has a sliver of the memory. If a kid needs a computer, get them a computer.

## Why it still works

Because it is a gateway, and it is cheap enough to not be precious. Same thing that made the old Pi work.

It boots straight into something a kid can touch. I put five little games on one, tic-tac-toe, connect four, minesweeper, hangman, and 2048, and posted the whole thing so any kid can flash it in about ten minutes. You tap a game, you play it, and then you open the file and change it. Make the X green. Put your friends' names in the hangman list. Make the Connect Four computer dumber so you can finally beat it. Rerun, and it lands on a real screen in your hand a second later. Change something, run it, see what happened, ask why. For a kid who has never coded, that is the whole job, and a cheap board with a screen is the shortest path I know to it.

And it is not stuck behind glass. The board has pins. Plug in a two-dollar temperature or light sensor and the screen starts reacting to the actual room instead of a made-up one. That jump, from "I changed the code" to "I changed the code and something in the real world answered," is where a lot of kids stop playing and start building. A phone can't do that. A school Chromebook can't do that. A fifteen-dollar board can.

And it is an on-ramp, not the last stop. The next step is a Pico for real electronics, or a Pi when they want a whole computer. A cheap start is not a small start.

## Where does this leave the next kid

Maybe the cheap Linux computer comes back when the memory market cools off. I hope it does. Until then, the door we can still hold open, for a classroom, for a family without a maker at home, for a kid who just wants to watch their idea light up, is a board that costs less than a video game.

And that kid will not be poking at it alone. These boards run Python, and there is a tool like Codex or Claude Code sitting right next to them now, explaining a file, making the change they asked for, catching the typo. Some people call that cheating. I think it is just what coding is, and a cheap board is the cheapest place there is to get good at it.

Get a board in front of a kid, flash the games, and let them start changing things. It got a lot of us here, and it should be within reach of the next kid too. That first "wait, I can just change it?" is the whole thing.

The games and the ten-minute setup are here: [github.com/MarioCruz/learn-to-code-arcade](https://github.com/MarioCruz/learn-to-code-arcade).

Mario the Maker

---

*A few links if you want to check the numbers: [Raspberry Pi's own note on the price rises](https://www.raspberrypi.com/news/more-memory-driven-price-rises/), [Jeff Geerling on what DRAM pricing is doing to cheap boards](https://www.jeffgeerling.com/blog/2026/dram-pricing-is-killing-the-hobbyist-sbc-market/), and [The Register's writeup](https://www.theregister.com/2026/02/02/raspberry_pi_ram_shortage_price_hike/).*
