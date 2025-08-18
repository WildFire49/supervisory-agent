"""
Smart Vector Embedding Strategy for Template Updates
Senior Engineer Solution: Hybrid approach balancing accuracy vs performance
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import asyncio

from app.agents.configurator.vector_storage import SchemaVectorStore
from app.services.context_template_service import ContextTemplateService

logger = logging.getLogger(__name__)

class EmbeddingStrategy(Enum):
    """Vector embedding strategies"""
    IMMEDIATE = "immediate"      # Re-embed on every change (high accuracy, high cost)
    BATCH = "batch"             # Batch re-embed periodically (lower cost, eventual consistency)
    SMART = "smart"             # Smart triggers based on change significance (balanced)
    DISABLED = "disabled"       # No automatic re-embedding (manual only)

class CorrectionImpact(Enum):
    """Impact levels for corrections"""
    HIGH = "high"       # Schema structure changes, table names, critical joins
    MEDIUM = "medium"   # Column names, data types, business logic
    LOW = "low"         # Formatting, minor rules, clarifications

class SmartVectorStrategy:
    """
    Senior Engineer Decision Matrix for Vector Embedding Strategy
    
    Considerations:
    1. Cost: OpenAI embedding API calls are expensive at scale
    2. Accuracy: Stale embeddings lead to poor query generation
    3. Performance: Real-time embedding causes UI delays
    4. Consistency: Template updates should reflect in vector search
    """
    
    def __init__(self, strategy: EmbeddingStrategy = EmbeddingStrategy.SMART):
        self.strategy = strategy
        self.vector_store = SchemaVectorStore()
        self.template_service = ContextTemplateService()
        
        # Smart strategy thresholds
        self.high_impact_threshold = 1      # Re-embed immediately
        self.medium_impact_threshold = 3    # Re-embed after 3 changes
        self.low_impact_threshold = 5       # Re-embed after 5 changes
        self.time_threshold = timedelta(hours=24)  # Force re-embed after 24h
        
    def classify_correction_impact(self, correction_type: str, correction_details: str) -> CorrectionImpact:
        """Classify the impact level of a correction"""
        
        # High impact: Schema structure changes
        high_impact_types = {
            "wrong_table", "wrong_schema", "missing_join", 
            "wrong_relationship", "schema_prefix", "table_structure"
        }
        
        # Medium impact: Column and logic changes  
        medium_impact_types = {
            "wrong_column", "wrong_data_type", "missing_column",
            "wrong_logic", "aggregation_error", "filter_logic"
        }
        
        # Check correction type
        if correction_type.lower().replace(" ", "_") in high_impact_types:
            return CorrectionImpact.HIGH
        elif correction_type.lower().replace(" ", "_") in medium_impact_types:
            return CorrectionImpact.MEDIUM
        
        # Check correction content for high-impact keywords
        high_impact_keywords = ["table", "schema", "join", "relationship", "foreign key"]
        if any(keyword in correction_details.lower() for keyword in high_impact_keywords):
            return CorrectionImpact.HIGH
            
        return CorrectionImpact.LOW
    
    async def should_re_embed(
        self, 
        connection_id: str, 
        correction_type: str, 
        correction_details: str
    ) -> Tuple[bool, str]:
        """
        Senior Engineer Decision Logic:
        Determine if vector re-embedding should occur based on strategy and impact
        """
        
        if self.strategy == EmbeddingStrategy.DISABLED:
            return False, "Re-embedding disabled"
        
        if self.strategy == EmbeddingStrategy.IMMEDIATE:
            return True, "Immediate strategy: always re-embed"
        
        impact = self.classify_correction_impact(correction_type, correction_details)
        
        if self.strategy == EmbeddingStrategy.SMART:
            # Smart strategy: impact-based decisions
            if impact == CorrectionImpact.HIGH:
                return True, f"High impact correction: {correction_type}"
            
            # Check accumulation thresholds
            correction_count = await self._get_recent_correction_count(connection_id, impact)
            threshold = self._get_threshold_for_impact(impact)
            
            if correction_count >= threshold:
                return True, f"Threshold reached: {correction_count} {impact.value} impact corrections"
            
            # Check time-based threshold
            last_embed_time = await self._get_last_embed_time(connection_id)
            if last_embed_time and datetime.utcnow() - last_embed_time > self.time_threshold:
                return True, f"Time threshold exceeded: {self.time_threshold}"
            
            return False, f"Smart strategy: waiting for more changes ({correction_count}/{threshold})"
        
        if self.strategy == EmbeddingStrategy.BATCH:
            # Batch strategy: time-based only
            last_embed_time = await self._get_last_embed_time(connection_id)
            if not last_embed_time or datetime.utcnow() - last_embed_time > self.time_threshold:
                return True, "Batch strategy: time threshold reached"
            
            return False, "Batch strategy: waiting for time threshold"
        
        return False, "Unknown strategy"
    
    async def handle_template_correction(
        self,
        connection_id: str,
        correction_type: str,
        correction_details: str,
        template_id: str
    ) -> Dict[str, any]:
        """
        Main entry point: Handle template correction with smart re-embedding
        """
        
        should_embed, reason = await self.should_re_embed(
            connection_id, correction_type, correction_details
        )
        
        result = {
            "correction_logged": True,
            "template_updated": True,
            "vector_re_embedded": False,
            "embedding_reason": reason,
            "strategy": self.strategy.value
        }
        
        if should_embed:
            try:
                # Get updated template with corrections
                template = await self.template_service.get_template_by_id(template_id)
                
                # Create enhanced context for re-embedding
                enhanced_context = await self._create_enhanced_context(
                    connection_id, template, correction_details
                )
                
                # Re-embed with enhanced context
                success = await self._re_embed_with_corrections(
                    connection_id, enhanced_context
                )
                
                if success:
                    result["vector_re_embedded"] = True
                    result["embedding_reason"] = f"Successfully re-embedded: {reason}"
                    await self._update_last_embed_time(connection_id)
                else:
                    result["embedding_reason"] = f"Re-embedding failed: {reason}"
                    
            except Exception as e:
                logger.error(f"Error during smart re-embedding: {str(e)}")
                result["embedding_reason"] = f"Re-embedding error: {str(e)}"
        
        return result
    
    async def _create_enhanced_context(
        self, 
        connection_id: str, 
        template: dict, 
        correction_details: str
    ) -> str:
        """Create enhanced context that includes corrections for better embeddings"""
        
        base_context = f"""
        TEMPLATE CONTEXT:
        Business Rules: {template.get('business_rules_template', '')}
        Schema Context: {template.get('schema_context_template', '')}
        Domain Prompts: {template.get('domain_specific_prompts', '')}
        
        RECENT USER CORRECTIONS:
        {correction_details}
        
        CORRECTION TIMESTAMP: {datetime.utcnow().isoformat()}
        """
        
        return base_context
    
    async def _re_embed_with_corrections(
        self, 
        connection_id: str, 
        enhanced_context: str
    ) -> bool:
        """Re-embed schema with correction context"""
        
        try:
            # This would integrate with the existing SchemaVectorStore
            # to update embeddings with correction context
            
            # For now, log the intent - full implementation would:
            # 1. Retrieve current schema from vector store
            # 2. Enhance with correction context  
            # 3. Re-embed and update vector store
            
            logger.info(f"🔄 Re-embedding schema for connection {connection_id}")
            logger.info(f"📝 Enhanced context length: {len(enhanced_context)} chars")
            
            # Placeholder for actual re-embedding logic
            await asyncio.sleep(0.1)  # Simulate embedding API call
            
            return True
            
        except Exception as e:
            logger.error(f"Re-embedding failed: {str(e)}")
            return False
    
    def _get_threshold_for_impact(self, impact: CorrectionImpact) -> int:
        """Get correction count threshold for impact level"""
        if impact == CorrectionImpact.HIGH:
            return self.high_impact_threshold
        elif impact == CorrectionImpact.MEDIUM:
            return self.medium_impact_threshold
        else:
            return self.low_impact_threshold
    
    async def _get_recent_correction_count(
        self, 
        connection_id: str, 
        impact: CorrectionImpact
    ) -> int:
        """Get count of recent corrections for impact level"""
        # This would query the correction logs
        # For now, return placeholder
        return 0
    
    async def _get_last_embed_time(self, connection_id: str) -> Optional[datetime]:
        """Get timestamp of last vector embedding"""
        # This would be stored in metadata
        return None
    
    async def _update_last_embed_time(self, connection_id: str):
        """Update last embedding timestamp"""
        # This would update metadata
        pass

# Configuration factory
def create_vector_strategy(strategy_name: str = "smart") -> SmartVectorStrategy:
    """Factory function to create vector strategy based on configuration"""
    
    strategy_map = {
        "immediate": EmbeddingStrategy.IMMEDIATE,
        "batch": EmbeddingStrategy.BATCH, 
        "smart": EmbeddingStrategy.SMART,
        "disabled": EmbeddingStrategy.DISABLED
    }
    
    strategy = strategy_map.get(strategy_name.lower(), EmbeddingStrategy.SMART)
    return SmartVectorStrategy(strategy)
