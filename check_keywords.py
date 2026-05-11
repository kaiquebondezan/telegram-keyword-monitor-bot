#!/usr/bin/env python3
"""
Script para verificar e migrar keywords no MongoDB.
Converte "added_at" para "created_at" e "updated_at" se necessário.
"""

import asyncio
from datetime import datetime, timezone
import motor.motor_asyncio
from config import MONGO_URI

async def main():
    print("\n" + "=" * 70)
    print("🔍 VERIFICADOR DE KEYWORDS - MongoDB")
    print("=" * 70)
    
    # Conecta ao MongoDB
    db_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    keywords_collection = db_client["telegram_keyword_bot"]["keywords"]
    
    try:
        # Conta total de keywords
        total = await keywords_collection.count_documents({})
        
        if total == 0:
            print("\n📭 Nenhuma keyword encontrada no MongoDB!")
            print("   Use /adicionar para adicionar palavras-chave")
            return
        
        print(f"\n✅ {total} keywords encontradas!")
        print("\nAnalisando documentos...\n")
        print("-" * 70)
        
        # Busca keywords
        docs = await keywords_collection.find({}).to_list(length=None)
        
        needs_migration = 0
        already_migrated = 0
        
        for doc in docs:
            keyword = doc.get("keyword", "???")
            has_created = "created_at" in doc
            has_updated = "updated_at" in doc
            has_added = "added_at" in doc
            
            status = "✅" if (has_created and has_updated) else "⚠️"
            
            if has_added:
                print(f"{status} {keyword:20} | Format: added_at (antigo)")
                needs_migration += 1
            elif has_created and has_updated:
                created = doc["created_at"].strftime("%d/%m/%Y %H:%M:%S")
                print(f"{status} {keyword:20} | Format: novo | Criada: {created}")
                already_migrated += 1
            else:
                print(f"⚠️  {keyword:20} | Format: incompleto (created: {has_created}, updated: {has_updated})")
                needs_migration += 1
        
        print("-" * 70)
        
        # Resume
        print(f"\n📊 Status:")
        print(f"  - Já migradas: {already_migrated} ✅")
        print(f"  - Precisam migrar: {needs_migration} ⚠️")
        
        # Migra se necessário
        if needs_migration > 0:
            print(f"\n🔧 Migrando {needs_migration} keywords...\n")
            now = datetime.now(timezone.utc)
            
            # Busca novamente para migrar
            cursor = keywords_collection.find({})
            migrated_count = 0
            
            async for doc in cursor:
                keyword = doc["keyword"]
                
                # Se tem added_at mas não tem created_at/updated_at
                if "added_at" in doc and "created_at" not in doc:
                    added_time = doc["added_at"]
                    await keywords_collection.update_one(
                        {"keyword": keyword},
                        {
                            "$set": {
                                "created_at": added_time,
                                "updated_at": added_time
                            },
                            "$unset": {"added_at": ""}  # Remove campo antigo
                        }
                    )
                    migrated_count += 1
                    print(f"  ✅ {keyword}: convertida de 'added_at' para 'created_at'/'updated_at'")
                
                # Se não tem created_at/updated_at
                elif "created_at" not in doc or "updated_at" not in doc:
                    update_dict = {}
                    if "created_at" not in doc:
                        update_dict["created_at"] = now
                    if "updated_at" not in doc:
                        update_dict["updated_at"] = now
                    
                    await keywords_collection.update_one(
                        {"keyword": keyword},
                        {"$set": update_dict}
                    )
                    migrated_count += 1
                    print(f"  ✅ {keyword}: timestamps adicionados")
            
            print(f"\n✅ {migrated_count} keywords migradas com sucesso!")
        else:
            print("\n✅ Todas as keywords já estão no formato novo!")
        
        # Info final
        print("\n" + "=" * 70)
        print("✨ Database de keywords está pronta!")
        print("=" * 70 + "\n")
        
        # Mostra exemplo de documento
        print("📋 Exemplo de documento após migração:")
        print("-" * 70)
        sample = await keywords_collection.find_one({})
        if sample:
            for key, value in sample.items():
                if key == "_id":
                    print(f"  {key}: ObjectId(...)")
                elif isinstance(value, datetime):
                    print(f"  {key}: ISODate('{value.isoformat()}Z')")
                else:
                    print(f"  {key}: '{value}'")
        print("-" * 70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Erro ao verificar keywords: {e}")
    finally:
        db_client.close()


if __name__ == "__main__":
    asyncio.run(main())
