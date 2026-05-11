#!/usr/bin/env python3
"""
Script unificado para verificar e migrar toda a database.
Valida sessão e keywords em um só comando.
"""

import asyncio
from datetime import datetime, timezone
import motor.motor_asyncio
from config import MONGO_URI

async def check_session(db):
    """Verifica e migra documento de sessão."""
    print("\n" + "=" * 70)
    print("🔐 VERIFICAÇÃO: SESSÃO TELEGRAM")
    print("=" * 70)
    
    session_col = db["session"]
    doc = await session_col.find_one({"_id": "session"})
    
    if not doc:
        print("\n❌ Nenhuma sessão encontrada!")
        print("   Execute: python setup_session.py")
        return False
    
    has_created = "created_at" in doc
    has_updated = "updated_at" in doc
    
    print("\n✅ Sessão encontrada!")
    print(f"   - created_at: {'✅' if has_created else '❌'}")
    print(f"   - updated_at: {'✅' if has_updated else '❌'}")
    
    if not has_created or not has_updated:
        print("\n   🔧 Migrando...")
        now = datetime.now(timezone.utc)
        update_dict = {}
        
        if not has_created:
            update_dict["created_at"] = now
        if not has_updated:
            update_dict["updated_at"] = now
        
        await session_col.update_one({"_id": "session"}, {"$set": update_dict})
        print("   ✅ Sessão migrada com sucesso!")
        return True
    
    print("\n✅ Sessão já possui todos os timestamps!")
    return True


async def check_keywords(db):
    """Verifica e migra documentos de keywords."""
    print("\n" + "=" * 70)
    print("📝 VERIFICAÇÃO: PALAVRAS-CHAVE")
    print("=" * 70)
    
    keywords_col = db["keywords"]
    total = await keywords_col.count_documents({})
    
    if total == 0:
        print("\n📭 Nenhuma keyword encontrada!")
        print("   Use /adicionar para adicionar palavras-chave")
        return True
    
    print(f"\n✅ {total} keywords encontradas!")
    
    # Analisa keywords
    needs_migration = 0
    docs = await keywords_col.find({}).to_list(length=None)
    
    for doc in docs:
        keyword = doc.get("keyword", "???")
        has_created = "created_at" in doc
        has_updated = "updated_at" in doc
        
        if not (has_created and has_updated):
            needs_migration += 1
            print(f"   ⚠️  {keyword:20} | Faltam timestamps")
    
    print(f"\n   📊 Status: {total - needs_migration}/{total} migradas")
    
    if needs_migration > 0:
        print(f"\n   🔧 Migrando {needs_migration} keywords...\n")
        now = datetime.now(timezone.utc)
        migrated = 0
        
        cursor = keywords_col.find({})
        async for doc in cursor:
            keyword = doc["keyword"]
            update_dict = {}
            
            # Converte added_at se existir
            if "added_at" in doc and "created_at" not in doc:
                added_time = doc["added_at"]
                update_dict["created_at"] = added_time
                update_dict["updated_at"] = added_time
                unset_dict = {"added_at": ""}
                await keywords_col.update_one(
                    {"keyword": keyword},
                    {"$set": update_dict, "$unset": unset_dict}
                )
            else:
                # Adiciona timestamps se faltarem
                if "created_at" not in doc:
                    update_dict["created_at"] = now
                if "updated_at" not in doc:
                    update_dict["updated_at"] = now
                
                if update_dict:
                    await keywords_col.update_one(
                        {"keyword": keyword},
                        {"$set": update_dict}
                    )
            
            if update_dict:
                migrated += 1
                print(f"      ✅ {keyword}")
        
        print(f"\n   ✅ {migrated} keywords migradas!")
    else:
        print("\n   ✅ Todas as keywords já possuem timestamps!")
    
    return True


async def main():
    print("\n" + "╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "🗄️  VERIFICADOR COMPLETO DE DATABASE" + " " * 18 + "║")
    print("╚" + "=" * 68 + "╝")
    
    db_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    db = db_client["telegram_keyword_bot"]
    
    try:
        # Verifica ambos
        session_ok = await check_session(db)
        keywords_ok = await check_keywords(db)
        
        # Resumo final
        print("\n" + "=" * 70)
        print("✨ RESUMO FINAL")
        print("=" * 70)
        print(f"  🔐 Sessão: {'✅ OK' if session_ok else '❌ ERRO'}")
        print(f"  📝 Keywords: {'✅ OK' if keywords_ok else '❌ ERRO'}")
        print("\n💡 Seu bot está pronto para rodar!")
        print("   Execute: python main.py")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Erro ao verificar database: {e}")
    finally:
        db_client.close()


if __name__ == "__main__":
    asyncio.run(main())
