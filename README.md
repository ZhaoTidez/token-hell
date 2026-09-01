# Token HELL

[中文版](README.zh.md)

## 1. Project Overview

### 1.1 Core Concept

**Token Survivors: The Context War** is an innovative indie game that blends bullet-hell shooting with language generation. Players control a cursor on a battlefield filled with falling vocabulary, collect English words to construct sentences, and interact with a large language model in real-time, experiencing the unique charm of "context warfare."

### 1.2 Setting

Deep within the digital world, a war over the essence of language is unfolding. Countless words rain down like meteors — some are normal English words, others are corrupted "garbled" tokens. As a "Context Warrior," you must shoot or absorb these words to build meaningful sentences, feed them to a large language model to receive replies, while dodging deadly bullet barrages.

### 1.3 Main Objectives

- **Survival Challenge**: Stay alive as long as possible through escalating bullet barrages
- **Sentence Construction**: Collect vocabulary to build coherent English sentences
- **Score Pursuit**: Earn high scores through correct replies and climb the leaderboard
- **Context War**: Interact with AI to create a unique gameplay experience based on model responses

<br />

***

## 2. Quick Start

### 2.1 API Configuration (Required Before First Run)

The game supports interacting with large language models via API. Before running for the first time, configure the `api_config.json` file:

```json
{
    "api_key": "your-api-key",
    "base_url": "https://api.deepseek.com/v1",
    "model": "deepseek-chat"
}
```

**Supported API Providers:**

| Provider | base_url Example | Notes |
| -------- | ---------------- | ----- |
| DeepSeek | `https://api.deepseek.com/v1` | Recommended, well-supported |
| OpenAI | `https://api.openai.com/v1` | Supported |
| Anthropic | `https://api.anthropic.com` | Supported |
| Other Compatible APIs | Varies by provider | Must support OpenAI-compatible format |

> If you don't configure an API key, the game can still run (using basic grammar checking), but the experience will be significantly reduced.

### 2.2 Controls

#### Keyboard

| Key | Function |
| --- | -------- |
| `↑ ↓ ← →` | Move cursor |
| `Z` | Shoot (knock down words) |
| `Enter` | Submit sentence to LLM |
| `Backspace` | Delete last added word |
| `Q` | Release skill (costs energy) |

#### Gameplay Goals

1. **Dodge Bullets**: Bullets constantly fly across the screen; getting hit reduces HP
2. **Collect Words**: Absorb falling words into the "Context Window" at the bottom
3. **Build Sentences**: Combine words into coherent English sentences
4. **Submit to AI**: Press Enter — the LLM evaluates your sentence and replies
5. **Control Temperature**: The longer you play, the higher the temperature, the more chaotic the bullets!
6. **Pursue Low PPL**: The more fluent your sentence, the lower the PPL, the higher the score!

<br />

***

## 3. Innovation & Unique Features

> "When bullet-hell meets language, when shooting becomes sentence-building — this game will completely change your perception!"

### 3.1 This Is Not Just a Bullet-Hell Game

#### Traditional Bullet-Hell vs. Context War

| What You Think Bullet-Hell Is | The Truth of Context War |
| ----------------------------- | ------------------------ |
| Frantically dodging bullets | Frantically collecting words |
| Killing enemies for points | Eating words and building sentences for points |
| Die and start over | The more you build sentences, the more cultured you get |
| Infinite repetitive despair | AI plays with you — every game is a new experience |

#### Your Brain Needs to Run on All Cylinders

- **Right hand controls movement**: Dodge bullets, maneuver
- **Left hand controls shooting**: Shoot down unwanted words
- **Brain builds sentences**: Think about how to form coherent English from collected words
- **Also deal with AI**: It evaluates your sentences and fires back at you

### 3.2 Let AI Be Your "Opponent" and "Teammate"

Imagine this scenario:

> You carefully construct: "I am happy to see you"
> Press Enter. AI responds: "True, That makes me happy too!"
> Then all the words from "That makes me happy too" start falling on screen
> You excitedly shoot them down one by one, each worth +50 points!
> LLM reply bonus: +100 points!
> Absolutely exhilarating!

Or this scenario:

> You randomly grab some words: "xkjl qwrt am happy"
> AI coldly responds: "False"
> Then a bunch of red garbled words come screaming in, the bullets are dense as rain...
> Eating garbled words costs points! What a loss!

**This is the magic of Context War: your language ability directly determines game difficulty!**

### 3.3 Overload System: Greed Has a Price

**Context Window** — Your sentence storage

- You can store up to **15 words**
- The more words you pack, the higher the "overload rate"
- At 100% overload, the window turns red as a warning!
- Garbled words significantly increase overload

**Do you frantically collect words for high scores? Or carefully select for quality? This dilemma will keep you hooked!**

### 3.4 Multi-Dimensional Scoring: Something for Every Play Style

**More than one way to rack up high scores**

| Scoring Method | Description | Best For |
| -------------- | ----------- | -------- |
| Shooting down words | +20~50 points each | Shooter playstyle |
| Eating words | +10~-10 points each | Strategic playstyle |
| Correct LLM reply | +100 points | Language playstyle |
| PPL scoring | More fluent sentences = higher base score | Academic playstyle |

### 3.5 Solving Traditional Game Pain Points

Tired of traditional bullet-hell games?

| Traditional Bullet-Hell | Context War Says: "I Got You!" |
| ----------------------- | ----------------------------- |
| Boring after a while, fixed patterns | AI random replies — every game is new |
| Shooting feels meaningless | Every bullet is a language decision! |
| Difficulty increased by adding more enemies | Temperature + Rank dual-dimension difficulty curve |
| Score is just a number | Score = PPL quality — learn English while gaming? |
| Forget everything when you die | Sentence-building ability is invisible growth |

***

## 4. Gameplay Details

### 4.1 Core Mechanics

#### 4.1.1 Player Controls

| Key | Function |
| --- | -------- |
| `↑ ↓ ← →` or `W A S D` | Move cursor |
| `Z` | Shoot (knock down words) |
| `Enter` | Submit sentence to LLM |
| `Backspace` | Delete last added word |
| `Q` | Release skill (costs energy) |

#### 4.1.2 Vocabulary System

Words in the game are categorized as follows:

| Type | Example | Color | Behavior |
| ---- | ------- | ----- | -------- |
| Content Noun | time, world, data, model | Cyan | Fires slow aimed bullets |
| Content Verb | runs, thinks, learns | Green | Fires slow aimed bullets |
| Content Adj | fast, deep, bright | Teal | Fires slow aimed bullets |
| Function Word | the, a, is, and | Yellow | Probability-based bullet firing |
| Noise Word | xkjl, qwrt, zxcv | Red | Fires high-difficulty bullets, toxic |

#### 4.1.3 Life System

- Starting lives: **2** (represented by hearts)
- Life recovery: Collecting life fragments adds **10%** to the life bar
- When life bar reaches **100%**, gain **1 extra life**
- Game over when lives reach zero
- **5 seconds of invincibility** after taking damage

### 4.2 Victory Conditions & Score Calculation

#### 4.2.1 Victory Conditions

This is an endless-mode game with no fixed victory conditions. Players aim to:

- **Survive longer**
- **Achieve higher scores**
- **Build more fluent sentences**

#### 4.2.2 Score Calculation

| Action | Score Change |
| ------ | ------------ |
| Correct LLM reply (True) | +100 points |
| Shooting down words from correct reply | +50 points/word |
| Eating normal words | +10 points |
| Shooting down normal words | +20 points |
| Eating garbled words | -10 points |

### 4.3 Main Flow

```
Game Start
    ↓
Enter API Key (optional, can skip)
    ↓
First Section Begins
    ↓
Words continuously fall → Player shoots/eats words
    ↓
Build sentence → Press Enter to submit
    ↓
LLM evaluates and replies
    ↓
Section Settlement → Calculate Score → Next Section
    ↓
Lives reach zero → Game Over → Display Final Score
```

### 4.4 Rank (Difficulty) System

- **Rank = Current Section number**, increases as the game progresses
- Effects:
  - Word drop speed increases
  - Bullet density increases
  - Garbled word appearance rate rises

### 4.5 LLM Interaction Logic

#### 4.5.1 Prompt Design

The prompt submitted to the LLM (English):

```
Please evaluate the following sentence: determine if it is understandable human language.
If yes, reply "True" followed by a response sentence.
If no, reply "False".
Must strictly follow this format: '{True}, {response sentence}' or '{False}'.
Do not output any additional text.
Keep the response sentence under 20 tokens.
```

#### 4.5.2 Response Processing

| Judgment | Subsequent Handling |
| -------- | ------------------- |
| **True** | All words from the response fall in order; each word worth +50 points, reply bonus +100 points |
| **False** | 5 + Rank garbled words fall, firing high-difficulty bullets |

#### 4.5.3 Fallback Handling

If the API call fails or the response format is incorrect:

- Display error notification
- Use basic grammar checking to evaluate sentence fluency
- Use pre-written fallback sentences

### 4.6 Bullet System

#### 4.6.1 Bullet Types

| Source | Difficulty | Characteristics |
| ------ | ---------- | --------------- |
| Normal word bullets | Medium | Slow, mainly aimed shots |
| Garbled word bullets | High | Fast, multi-directional spread |
| Reply word bullets | Easy | Slow aimed shots |

#### 4.6.2 Bullet API

```python
createBullet(color, velocity, angle, aimplayer)
```

- **angle**: 0-360 degrees
- **aimplayer=true**: angle is the offset from the direction pointing at the player
- **aimplayer=false**: angle is the absolute angle (0 = right, counterclockwise rotation)

***

## 5. Technical Details

### 5.1 Requirements

#### 5.1.1 Operating System

- **Windows 10/11** (primary testing platform)
- macOS / Linux (theoretically compatible, untested)

#### 5.1.2 Runtime

**Python Version**: Python 3.10 or higher

**Core Dependencies**:

```
pygame>=2.0.0
```

**Optional Dependencies** (for local PPL calculation):

```
torch>=1.10.0
transformers>=4.20.0
```

#### 5.1.3 API Support

The game supports interacting with large language models via API. You can configure:

- DeepSeek
- OpenAI
- Anthropic
- Any OpenAI-compatible API

### 5.2 Build & Run Instructions

#### 5.2.1 Install Dependencies

```bash
# Install core dependencies
pip install pygame

# Optional: Install AI support (for local PPL calculation)
pip install torch transformers
```

#### 5.2.2 API Configuration

On first run, the game reads the `api_config.json` configuration file:

```json
{
    "api_key": "your-api-key",
    "base_url": "url",
    "model": "model"
}
```

Supported API providers:

- DeepSeek
- OpenAI
- Anthropic
- Any OpenAI-compatible API

You can also choose to **run without an API** (using basic grammar checking).

### 5.3 Module Overview

#### 5.3.1 Core Modules

| Module | File | Description |
| ------ | ---- | ----------- |
| Main Game Loop | context_war.py | Entry point, game loop control |
| Vocabulary System | Built-in | Token class manages word drops and behavior |
| Bullet System | Built-in | Bullet class manages bullet spawning and collision |
| Particle System | Particle class | Visual effect particles (explosions, effects, etc.) |

#### 5.3.2 AI Integration

| Module | Class | Description |
| ------ | ----- | ----------- |
| PPL Scoring | PPLScorer | Calculates perplexity to evaluate language quality |
| API Calls | Built-in | Interacts with LLM API for replies |
| Fallback Logic | Built-in | Basic grammar checking when API fails |

#### 5.3.3 Game Systems

| System | Description |
| ------ | ----------- |
| Temperature System | TemperatureSystem — increases over time, affecting difficulty and bullet behavior |
| Context Window | ContextWindow — stores the player's constructed sentences |
| Life System | Player — manages health, invincibility, etc. |
| Skill System | Player — Q-key skill mechanism |

***

## 6. AI Tool Usage

### 6.1 AI Tools Used

| AI Tool | Primary Use |
| ------- | ----------- |
| **Gemini** | Project concept & innovation design |
| **GLM-5.1** | Core code implementation |
| **GPT** | Code tuning & optimization |

### 6.2 Human-Completed Work

#### 6.2.1 Initial Project Concept

- Core game concept design: **"Context War" theme**
- The idea of blending bullet-hell shooting with language generation
- Vocabulary classification system (Content Noun/Verb/Adj, Function Word, Noise Word)
- LLM interaction prompt template design
- Temperature system and hallucination event mechanism design

#### 6.2.2 Key Innovation Design

- **Rank System**: Progressive section-based difficulty scaling
- **Temperature System**: Time-driven dynamic difficulty curve
- **Multi-layered Scoring**: PPL-based language quality assessment
- **Overload Mechanism**: Context window capacity pressure
- **Hallucination Event System**: High temperature triggers various abnormal effects

### 6.3 AI-Completed Work

#### 6.3.1 Gemini — Development Detail Implementation

Interacted with Gemini to complete:

- **Bullet API Design**: Defined `createBullet(color, velocity, angle, aimplayer)` interface
- **Particle Effects**: Explosions, visual enhancements
- **Collision Detection Optimization**: Balancing performance and accuracy
- **UX Details**: Invincibility frames, visual feedback

#### 6.3.2 GLM-5.1 — Core Code Implementation

Used GLM-5.1 for:

- **Main Game Loop Architecture**: State management and frame rate control
- **Player Class**: Movement, shooting, skill system
- **TokenBullet Class**: Word movement, AI behavior, bullet firing
- **ContextWindow Class**: Sentence building, display, submission logic
- **PPLScorer Class**: Perplexity calculation and scoring system
- **Temperature System**: Dynamic difficulty curve implementation
- **API Call Logic**: Multi-backend support and error handling

#### 6.3.3 GPT — Code Tuning & Optimization

Interacted with GPT for:

- **Performance Optimization**: Reducing memory usage, optimizing rendering
- **Code Refactoring**: Improving readability and maintainability
- **Edge Case Handling**: Empty input, timeouts, format errors
- **More Bullet Pattern Design**: Enriching visual effects
- **Game Balance Tuning**: Score system and life mechanic fine-tuning
