### **1\. Project Objective**

Now that your project has been assigned, your goal is to move from the "what" to the "how." You will produce a professional-grade **Design Document** that outlines the logic, architecture, and data structures of your system.

### **2\. Required Sections**

Your document must be organized with the following headings:

#### **I. Executive Summary & Problem Scope**

* **The Problem** (What specific technical or community challenge does this project address?): It’s hard for people to find a group of exactly 4 people who want to, and know how to play Euchre. A lot of existing Euchre bots cheat, or rely on very simple, hard-coded logic that is easily exploited by human competitors. The goal is to create a Euchre bot that plays competently and realistically, without using more knowledge than a human player would have.  
* **The Solution** (A high-level description of your software or IT system): ISMCTS (Information Set Monte Carlo Search Trees) is the current best and most commonly used algorithm for imperfect games. An imperfect game is a game with hidden information; ie, a game missing the full set of information (in the case of many card games, it would be the unknown position of some or most cards, due to a lack of knowledge of the cards that the other players have). ISMCTS is like MCTS, but with an extra step (determinization). MCTS utilizes a concept called “minimaxing”. In minimaxing, the algorithm creates a game tree of all possible future moves, and decides on the move which maximizes its potential score ([here](https://youtu.be/IQLkPgkLMNg?t=224) is an explanation on youtube). MCTS preforms best on solved games (such as Tic Tac Toe, Chess), whereas ISMCTS is best for games without perfect information sets. In the case of Euchre, the hidden information would be the cards in the kitty and the cards in the other players’ hands. Using ISMCTS, the bot is able to come up with the best possible play for its current situation with its current world knowledge (ie, knowledge, or lack thereof, of the cards that the other players have). There are 4 steps to ISMCTS: determinization, selection, expansion/simulation, and backpropagation.  
* **Target User** (Define exactly who will use this. e.g., "High school administrators tracking attendance" vs. "Students looking for tutoring"): People who want to play Euchre but don’t have enough players. Or, an app (like *Trickster Cards*) that has daily challenges, etc, which could use bots.

#### **II. Technical Requirements**

* **Functional Requirements** (What must the system do? e.g., "The system must allow users to reset passwords via email."): The system must first allow the user to play a game of Euchre. The user should be able to play cards, bid, discard, play a new game, and quit the game. The system should be able to shuffle and deal cards (Euchre is typically dealt in a (2,3)x2, (3,2)x2 pattern, or the reverse of that) and then flip up the top card. The game should display the current Trump, the dealer, and who bid. The score should be kept track of. The system must not allow any players (human or bot) to make illegal moves or bids. The Bowers must be identified and handled properly. Tricks must be taken correctly. The card distributions that are determinized must be consistent with current world knowledge (the bot’s knowledge must update for the cards that have been played). The system should use UCT to select the best move (highest simulated win probability).  
* **Non-Functional Requirements** (How must the system perform? e.g., "The app should load in under 2 seconds" or "The database must be encrypted."): The bot should make a play in a reasonable amount of time (between 1-5 seconds). There should be an Easy/Hard mode (though this will depend on computing power and speed) \- the easier the mode, the less iterations the bot will do. The system should be “seeded”; this will allow for the replay and analysis of a certain scenario. The system should be able to handle edge-case states. The UI should be understandable and easy, and it should look good *enough* (later tho).

#### **III. System Architecture & Logic**

This is the most critical section. You must include a visual representation of how your system works.

* **Logic Flowchart** (A step-by-step map of how a user moves through your application):  
  * Start: deck is built, shuffled, and distributed to players. Next card becomes the upcard and the remaining 3 become the kitty.  
  * Bidding: The player on the left of the “dealer” starts the bidding and it goes around clockwise. Players either Order Up or Pass. If everyone passes in the first phase then it will go around again and the players can choose suits. Dealer will be “stuck” at the end (stick the dealer) and have to choose a trump suit.  
  * Gameplay Loop: The first playing player to the left of the dealer leads. Everyone must follow suit, unless they are unable to. Hierarchy for winning tricks goes: A, K, Q, J, 10, 9\. A trump beats all non trump. In trump, the R/L bowers are high (minus one jack from the “next” suit in trump)  
    * User Turn: player selects and plays a valid card  
    * Bot Turn: Bot uses the ISMCTS simulation to decide on and play the best valid card  
  * Scoring: The system adds up the score after the game is done  
  * End: Once a team gets to 10+ points, they win the game.  
* **System Diagram** (If your project involves a frontend, backend, and database, show how they communicate): The frontend will display the score, cards, bidding, etc. The game controller will handle the game actions (it will know the full state of the world, handle the deck, and ensure there are no illegal moves \[and ensure the bots/players can’t cheat\]). The ISMCTS engine will clone the game with the bots current world knowledge and determinize the world (randomly distribute the unknown cards to the other 3 players), and then run the MCTS algorithm. The ISMCTS should also be receiving updates of the cards that have been played so that the plays it makes make sense.

#### **IV. Data Schema & Tech Stack**

* **Tech Stack** (List the languages, frameworks, and tools you will use (e.g., Python, React, Firebase). Justify *why* you chose these):   
* **Data Model** (Define what data you are collecting and how it’s organized):  
  * Cards will have Suit (S, H, D, C), Rank (A, K, Q, J, 10, 9), and Weight (Trump \> other, and within Trump: Right Bower \> Left \> Ace Trump \> King Trump \> Queen Trump \> 10 Trump \> 9 Trump. Outside of Trump, normal hierarchy).  
  * In the game there will be the:  
    * Visible hand  
    * Played cards  
    * Trump suit  
    * Current trick  
    * Pool of unknown cards  
  * Tree nodes: move, wins, visits, availability

### **V. Open Questions & Potential Problems**

A perfect plan is a dangerous one. This section proves you are thinking ahead about the "what-ifs."

#### **1\. Open Questions (The "Known Unknowns")**

List at least **three** technical or design questions you haven't answered yet. These are things you need to research or test before you can finish the project.

* Should bidding be part of the ISMCTS simulation, or should it be based off of ranking the cards and points and deciding how to bid based on heuristics?  
* Should the bot need to track "negative information"? (eg if player B didn't follow suit in Diamonds, they definitely have none.) This inference logic in the determinization step will make the bot much stronger, but it would add complexity to the "Randomize" function.  
* Will the bot be viable on a phone, or just a computer? \- can a smartphone CPU handle thousands of simulations in \<2 seconds without draining the battery?  
* How can we make the bot work with its partner? In Euchre, a human player knows how to work together with their partner and what they should lead or when to trump, etc. for example \- not trumping the ace of your partner. If your partner has won a trick, don’t take it unless the next person will take it from them. Etc.  
* How will we handle the bot going alone (2v2 to a 1v2, and therefore unable to rely on their partner for any tricks/unable to cooperate), or the bot defending against a loner?

#### **2\. Risk Assessment & Mitigation Table**

Identify three potential "points of failure" and how you will handle them.

| Potential Problem (Risk) | Impact (Low/Med/High) | Mitigation Plan (The "Fix") |
| :---- | :---- | :---- |
| **Computing Power:** if we don’t have enough computing power, the bot will make slow, poor decisions. | High | Have as many “forced” plays as possible to not waste computing power. And, hopefully, build a cluster to handle it. And to prevent exhausting the resources, delete trees that can no longer be continued based on updated world knowledge. |
| **Bad plays:** random playouts might add enough noise that the bot decides to play a ridiculous move. | Medium | The bot should have some basic guidelines (like if you’re guaranteed to lose a trick, throw a junk card, or, generally don’t trump your partner’s Ace). |
| **Exploitability:** The bot might end up with a tendency to make the same play or type of plays when put into a similar situation \- and a human player would be able to exploit this. | Medium-High | If the best options are within 1-5% of each other in terms of win rate, occasionally shuffle the option that the bot picks: this will introduce enough noise that the human players would less reliably be able to predict the bot. |

I put comments where I used AI \- I reworded everything the AI gave me and didn’t include anything I didn’t understand. Asked the AI for some additional risks or questions I was maybe overlooking. Had the AI expand on my ideas and included the useful stuff that it gave.

\-Matt S
