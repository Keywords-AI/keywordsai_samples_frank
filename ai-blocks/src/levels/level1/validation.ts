// src/levels/level1/validation.ts
/**
 * Level 1 Validation Logic - Meeting Scheduler
 */

import { Graph } from "../../engine/graph";
import { ValidationResult, LevelValidator, LevelAnswer } from "../types";
import { LEVEL_1_CONFIG, LEVEL_1_PRIMARY_ANSWER } from "./config";

export class Level1Validator implements LevelValidator {
  
  validate(graph: Graph): ValidationResult {
    // Level 1 now has only ONE perfect answer - but we give partial credit for close attempts
    return this.validateWithPartialCredit(graph, LEVEL_1_PRIMARY_ANSWER);
  }

  getHints(): string[] {
    return [
      "💡 Start with User Input to receive requests like 'tomorrow at 2pm'",
      "📅 Context Variable provides current date/time so AI understands 'tomorrow'",
      "🔗 Context Merge combines user request with current context",
      "🤖 LLM Parse can now understand relative dates with full context", 
      "📋 Google Calendar Get checks existing schedule for conflicts",
      "⏰ LLM Suggest Time finds available slots (needs calendar data!)",
      "📅 Google Calendar Schedule creates the actual event",
      "📝 LLM Text Output gives friendly confirmation to user",
      "🎯 Essential flow: User Input + Context Variable → Context Merge → LLM Parse → Google Calendar Get → LLM Suggest Time → Google Calendar Schedule → LLM Text Output",
      "⚡ All 8 blocks required - context is crucial for understanding relative dates!"
    ];
  }

  isUnlocked(completedLevels: number[]): boolean {
    // Level 1 is always unlocked (it's the first level)
    return true;
  }

  // Removed old validation method - replaced with partial credit system

  private validateWithPartialCredit(graph: Graph, perfectAnswer: LevelAnswer): ValidationResult {
    const result: ValidationResult = {
      isCorrect: false,
      score: 0,
      correctAspects: [],
      issues: [],
      hints: [],
      message: ""
    };

    // Extract block types from graph (filter out invalid nodes)
    const userBlocks = graph.nodes
      .map(node => node.type)
      .filter(type => type && typeof type === 'string');
    const userConnections = this.extractConnections(graph);

    // Check 1: Required blocks present (40 points - most important)
    const missingBlocks = perfectAnswer.requiredBlocks.filter(block => !userBlocks.includes(block));
    const extraBlocks = userBlocks.filter(block => !perfectAnswer.requiredBlocks.includes(block));
    
    if (missingBlocks.length === 0 && extraBlocks.length === 0) {
      result.correctAspects.push("✅ Perfect block selection - exactly the right 5 blocks!");
      result.score += 40;
    } else if (missingBlocks.length === 0) {
      result.correctAspects.push("✅ All required blocks present");
      result.score += 30; // Partial credit for extra blocks
      result.issues.push(`⚠️ Extra blocks detected: ${extraBlocks.join(", ")} - try to use only what's needed`);
    } else {
      const presentBlocks = perfectAnswer.requiredBlocks.filter(block => userBlocks.includes(block));
      if (presentBlocks.length > 0) {
        result.correctAspects.push(`✅ Some correct blocks: ${presentBlocks.join(", ")}`);
        result.score += Math.floor((presentBlocks.length / perfectAnswer.requiredBlocks.length) * 30);
      }
      result.issues.push(`❌ Missing essential blocks: ${missingBlocks.join(", ")}`);
      result.hints.push(`💡 Add these blocks: ${missingBlocks.join(", ")}`);
    }

    // Check 2: Exact block count (10 points)
    if (userBlocks.length === perfectAnswer.requiredBlocks.length) {
      result.correctAspects.push("✅ Perfect pipeline length");
      result.score += 10;
    } else if (userBlocks.length >= perfectAnswer.minBlocks && userBlocks.length <= perfectAnswer.maxBlocks) {
      result.correctAspects.push("✅ Reasonable pipeline length");
      result.score += 5; // Partial credit
    } else if (userBlocks.length < perfectAnswer.minBlocks) {
      result.issues.push(`❌ Pipeline too short (${userBlocks.length}/${perfectAnswer.minBlocks} minimum)`);
      result.hints.push("💡 Add more blocks to complete the workflow");
    } else {
      result.issues.push(`❌ Pipeline too long (${userBlocks.length}/${perfectAnswer.maxBlocks} maximum)`);
      result.hints.push("💡 Remove unnecessary blocks - keep it simple!");
    }

    // Check 3: Required connections (40 points - very important)
    const missingConnections = perfectAnswer.requiredConnections.filter(conn => 
      !userConnections.some(userConn => userConn.from === conn.from && userConn.to === conn.to)
    );
    
    if (missingConnections.length === 0) {
      result.correctAspects.push("✅ Perfect connections - data flows correctly!");
      result.score += 40;
    } else {
      const correctConnections = perfectAnswer.requiredConnections.filter(conn =>
        userConnections.some(userConn => userConn.from === conn.from && userConn.to === conn.to)
      );
      if (correctConnections.length > 0) {
        result.correctAspects.push(`✅ Some correct connections (${correctConnections.length}/${perfectAnswer.requiredConnections.length})`);
        result.score += Math.floor((correctConnections.length / perfectAnswer.requiredConnections.length) * 35);
      }
      result.issues.push(`❌ Missing connections: ${missingConnections.map(c => `${c.from} → ${c.to}`).join(", ")}`);
      result.hints.push("💡 Check your connections - follow the logical flow!");
    }

    // Check 4: Pipeline flow logic (10 points)
    const hasValidFlow = this.validatePipelineFlow(userBlocks, userConnections);
    if (hasValidFlow) {
      result.correctAspects.push("✅ Logical workflow structure");
      result.score += 10;
    } else {
      result.issues.push("❌ Workflow structure needs work");
      result.hints.push("💡 Build complete workflow: Input → Understand → Decide → Act → Output using ALL blocks");
    }

    // Perfect score only for exact match
    result.isCorrect = result.score === 100 && 
                      missingBlocks.length === 0 && 
                      extraBlocks.length === 0 &&
                      missingConnections.length === 0;

    // Generate feedback message
    if (result.isCorrect) {
      result.message = `🎉 PERFECT! You've mastered the art of workflow building. This is exactly how a meeting scheduler workflow should work using all blocks!`;
    } else if (result.score >= 80) {
      result.message = "🔥 So close to perfection! Just a few small adjustments needed.";
    } else if (result.score >= 60) {
      result.message = "👍 Good progress! You understand the basic flow - now refine the details.";
    } else if (result.score >= 30) {
      result.message = "💪 You're on the right track! Keep building - you've got some pieces right.";
         } else {
       result.message = "🎯 Build the complete workflow using ALL blocks: User Input + Context Variable → Context Merge → LLM Parse → Google Calendar Get → LLM Suggest Time → Google Calendar Schedule → User Output";
     }

    return result;
  }

  private extractConnections(graph: Graph): Array<{ from: string; to: string }> {
    const connections: Array<{ from: string; to: string }> = [];
    
    for (const edge of graph.edges) {
      const sourceNode = graph.nodes.find(n => n.id === edge.source);
      const targetNode = graph.nodes.find(n => n.id === edge.target);
      
      if (sourceNode && targetNode && sourceNode.type && targetNode.type) {
        connections.push({
          from: sourceNode.type,
          to: targetNode.type
        });
      }
    }
    
    return connections;
  }

  private validatePipelineFlow(blocks: string[], connections: Array<{ from: string; to: string }>): boolean {
    // Check for basic flow patterns
    const hasInputStart = blocks.includes("userInput") || blocks.includes("contextVariable");
    const hasAiProcessing = blocks.some(block => block && typeof block === 'string' && block.startsWith("llm"));
    const hasOutput = blocks.includes("userOutput");
    
    // Check that there are no isolated blocks (all blocks should be connected)
    const connectedBlocks = new Set<string>();
    connections.forEach(conn => {
      connectedBlocks.add(conn.from);
      connectedBlocks.add(conn.to);
    });
    
    const isolatedBlocks = blocks.filter(block => !connectedBlocks.has(block));
    
    return hasInputStart && hasAiProcessing && hasOutput && isolatedBlocks.length === 0;
  }
}

// Export singleton instance
export const level1Validator = new Level1Validator(); 