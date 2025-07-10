# Level System

This directory contains the organized level system for AI Blocks. Each level is self-contained with its own configuration, validation logic, and objectives.

## Structure

```
src/levels/
├── types.ts          # Common interfaces for all levels
├── index.ts          # Level system manager and registry
├── README.md         # This documentation
└── level1/           # Level 1 - Meeting Scheduler
    ├── config.ts     # Level configuration and answers
    └── validation.ts # Level-specific validation logic
```

## Current Levels

### Level 1: Meeting Scheduler
- **Goal**: Build a workflow using all blocks that schedules meetings
- **Blocks**: User Input → LLM Parse → LLM Suggest Time → Google Calendar Schedule → LLM Text Output
- **Alternative**: Enhanced version with Context Variable and Context Merge
- **Difficulty**: 1 (Beginner)

## Adding New Levels

To add a new level (e.g., Level 2):

1. **Create directory structure**:
   ```
   mkdir src/levels/level2
   ```

2. **Create config file** (`src/levels/level2/config.ts`):
   ```typescript
   import { LevelConfig, LevelAnswer } from "../types";
   
   export const LEVEL_2_PRIMARY_ANSWER: LevelAnswer = {
     requiredBlocks: ["block1", "block2", "block3"],
     requiredConnections: [
       { from: "block1", to: "block2" },
       { from: "block2", to: "block3" }
     ],
     minBlocks: 3,
     maxBlocks: 6,
     description: "Description of what this workflow achieves"
   };
   
   export const LEVEL_2_CONFIG: LevelConfig = {
     id: 2,
     title: "Level 2 Title",
     description: "What the user will learn",
     availableBlocks: ["block1", "block2", "block3"],
     answers: [LEVEL_2_PRIMARY_ANSWER],
     objectives: ["Learning objective 1", "Learning objective 2"],
     difficulty: 2
   };
   ```

3. **Create validation logic** (`src/levels/level2/validation.ts`):
   ```typescript
   import { Graph } from "../../engine/graph";
   import { ValidationResult, LevelValidator } from "../types";
   import { LEVEL_2_CONFIG } from "./config";
   
   export class Level2Validator implements LevelValidator {
     validate(graph: Graph): ValidationResult {
       // Your validation logic here
     }
     
     getHints(): string[] {
       return ["Hint 1", "Hint 2"];
     }
     
     isUnlocked(completedLevels: number[]): boolean {
       return completedLevels.includes(1); // Requires Level 1 completion
     }
   }
   
   export const level2Validator = new Level2Validator();
   ```

4. **Register the level** in `src/levels/index.ts`:
   ```typescript
   import { LEVEL_2_CONFIG } from "./level2/config";
   import { level2Validator } from "./level2/validation";
   
   const LEVEL_CONFIGS: Record<number, LevelConfig> = {
     1: LEVEL_1_CONFIG,
     2: LEVEL_2_CONFIG,  // Add this line
   };
   
   const LEVEL_VALIDATORS: Record<number, LevelValidator> = {
     1: level1Validator,
     2: level2Validator, // Add this line
   };
   ```

## Key Features

- **Modular**: Each level is completely self-contained
- **Extensible**: Easy to add new levels without affecting existing ones
- **Flexible**: Support for multiple correct answers per level
- **Progressive**: Levels can have unlock requirements
- **Educational**: Built-in hints and learning objectives

## Level Design Guidelines

1. **Clear Objectives**: Each level should teach specific concepts
2. **Multiple Solutions**: Allow alternative approaches when appropriate
3. **Progressive Difficulty**: Each level should build on previous knowledge
4. **Helpful Feedback**: Provide specific hints for common mistakes
5. **Real-world Relevance**: Use practical examples users can relate to 