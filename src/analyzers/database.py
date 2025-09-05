"""Database Schema and Structure Analyzer"""
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from src.core.base import BaseAnalyzer
from src.core.models import ScanResult, AnalysisResult


from src.core.logger import get_logger
class DatabaseAnalyzer(BaseAnalyzer):
    """Analyze database schemas, migrations, and ORM models"""
    
    name = "database"
    description = "Extract database schemas, tables, and relationships"

    logger = get_logger("database")
    
    # SQL patterns for different databases
    SQL_PATTERNS = {
        'create_table': re.compile(
            r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?["`]?(\w+)["`]?',
            re.IGNORECASE
        ),
        'alter_table': re.compile(
            r'ALTER\s+TABLE\s+["`]?(\w+)["`]?',
            re.IGNORECASE
        ),
        'index': re.compile(
            r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+["`]?(\w+)["`]?\s+ON\s+["`]?(\w+)["`]?',
            re.IGNORECASE
        ),
        'foreign_key': re.compile(
            r'FOREIGN\s+KEY.*?REFERENCES\s+["`]?(\w+)["`]?',
            re.IGNORECASE
        )
    }
    
    async def analyze(self, scan_result: ScanResult) -> AnalysisResult:
        """Analyze database structure"""
        tables = []
        migrations = []
        orm_models = []
        relationships = []
        
        for file_info in scan_result.files:
            # SQL files
            if file_info.extension == '.sql':
                sql_data = self._analyze_sql_file(file_info.path)
                tables.extend(sql_data['tables'])
                relationships.extend(sql_data['relationships'])
                
            # Migrations
            elif 'migration' in str(file_info.path).lower():
                migrations.append({
                    'file': file_info.path.name,
                    'type': self._detect_migration_type(file_info.path)
                })
                
            # ORM Models
            elif file_info.extension in ['.py', '.js', '.ts']:
                models = self._extract_orm_models(file_info.path)
                orm_models.extend(models)
        
        # Database type detection
        db_type = self._detect_database_type(scan_result)
        
        # Analyze Prisma schema
        prisma_schema = self._analyze_prisma_schema(scan_result)
        
        return AnalysisResult(
            analyzer=self.name,
            data={
                "database_type": db_type,
                "tables": list(set(tables))[:50],
                "migrations": migrations[:30],
                "orm_models": orm_models[:30],
                "relationships": relationships[:20],
                "prisma_schema": prisma_schema,
                "statistics": {
                    "total_tables": len(set(tables)),
                    "total_migrations": len(migrations),
                    "total_models": len(orm_models),
                    "has_relationships": len(relationships) > 0
                },
                "features": {
                    "has_migrations": len(migrations) > 0,
                    "has_orm": len(orm_models) > 0,
                    "has_prisma": prisma_schema is not None,
                    "has_indexes": self._check_indexes(scan_result)
                }
            }
        )
    
    def _analyze_sql_file(self, file_path: Path) -> Dict:
        """Extract tables and relationships from SQL files"""
        tables = []
        relationships = []
        
        try:
            content = file_path.read_text(errors='ignore')
            
            # Find tables
            for match in self.SQL_PATTERNS['create_table'].finditer(content):
                tables.append(match.group(1))
            
            # Find foreign keys (relationships)
            for match in self.SQL_PATTERNS['foreign_key'].finditer(content):
                relationships.append({
                    'type': 'foreign_key',
                    'target': match.group(1)
                })
                
        except Exception:
            pass
            
        return {'tables': tables, 'relationships': relationships}
    
    def _extract_orm_models(self, file_path: Path) -> List[Dict]:
        """Extract ORM model definitions"""
        models = []
        
        try:
            content = file_path.read_text(errors='ignore')
            
            # Django models
            if 'models.Model' in content:
                for match in re.finditer(r'class\s+(\w+)\(.*Model.*\)', content):
                    models.append({
                        'name': match.group(1),
                        'type': 'django',
                        'file': file_path.name
                    })
            
            # SQLAlchemy models
            elif 'Base = declarative_base' in content or 'db.Model' in content:
                for match in re.finditer(r'class\s+(\w+)\(.*(?:Base|db\.Model).*\)', content):
                    models.append({
                        'name': match.group(1),
                        'type': 'sqlalchemy',
                        'file': file_path.name
                    })
            
            # Sequelize models
            elif 'sequelize.define' in content:
                for match in re.finditer(r'sequelize\.define\([\'"](\w+)[\'"]', content):
                    models.append({
                        'name': match.group(1),
                        'type': 'sequelize',
                        'file': file_path.name
                    })
            
            # TypeORM entities
            elif '@Entity' in content:
                for match in re.finditer(r'@Entity.*?class\s+(\w+)', content, re.DOTALL):
                    models.append({
                        'name': match.group(1),
                        'type': 'typeorm',
                        'file': file_path.name
                    })
                    
        except Exception:
            pass
            
        return models[:10]  # Limit per file
    
    def _detect_migration_type(self, file_path: Path) -> str:
        """Detect migration tool type"""
        path_str = str(file_path).lower()
        
        if 'alembic' in path_str:
            return 'alembic'
        elif 'django' in path_str or re.match(r'^\d{4}_', file_path.name):
            return 'django'
        elif 'laravel' in path_str:
            return 'laravel'
        elif 'flyway' in path_str:
            return 'flyway'
        elif 'knex' in path_str:
            return 'knex'
        else:
            return 'unknown'
    
    def _detect_database_type(self, scan_result: ScanResult) -> str:
        """Detect database type from files"""
        for file_info in scan_result.files:
            if file_info.extension == '.sql':
                try:
                    content = file_info.path.read_text(errors='ignore')[:1000]
                    
                    if 'ENGINE=InnoDB' in content or 'AUTO_INCREMENT' in content:
                        return 'mysql'
                    elif 'SERIAL' in content or '::' in content:
                        return 'postgresql'
                    elif 'AUTOINCREMENT' in content:
                        return 'sqlite'
                    elif 'GO\n' in content:
                        return 'mssql'
                except Exception as e:
                    self.logger.debug(f"Error in SQL file type detection: {e}")
                    
        # Check config files
        for file_info in scan_result.files:
            if file_info.path.name in ['database.yml', 'database.json', 'ormconfig.json']:
                try:
                    content = file_info.path.read_text()
                    if 'mysql' in content.lower():
                        return 'mysql'
                    elif 'postgres' in content.lower():
                        return 'postgresql'
                    elif 'mongodb' in content.lower():
                        return 'mongodb'
                except Exception as e:
                    self.logger.debug(f"Error in config file database detection: {e}")
                    
        return 'unknown'
    
    def _analyze_prisma_schema(self, scan_result: ScanResult) -> Optional[Dict]:
        """Analyze Prisma schema if exists"""
        for file_info in scan_result.files:
            if file_info.path.name == 'schema.prisma':
                try:
                    content = file_info.path.read_text()
                    models = re.findall(r'model\s+(\w+)\s*{', content)
                    datasource = re.search(r'provider\s*=\s*"([^"]+)"', content)
                    
                    return {
                        'models': models[:20],
                        'datasource': datasource.group(1) if datasource else None,
                        'model_count': len(models)
                    }
                except Exception as e:
                    self.logger.debug(f"Error in Prisma schema analysis: {e}")
                    
        return None
    
    def _check_indexes(self, scan_result: ScanResult) -> bool:
        """Check if database has indexes defined"""
        for file_info in scan_result.files[:50]:
            if file_info.extension == '.sql':
                try:
                    content = file_info.path.read_text(errors='ignore')
                    if re.search(r'CREATE\s+(?:UNIQUE\s+)?INDEX', content, re.I):
                        return True
                except Exception as e:
                    self.logger.debug(f"Error in index detection: {e}")
        return False
