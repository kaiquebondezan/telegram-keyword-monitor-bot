#!/usr/bin/env python3
"""
Script para verificar e migrar documentos de sessão no MongoDB.
Adiciona created_at e updated_at se não existirem.
"""

import asyncio
from datetime import datetime, timezone
import motor.motor_asyncio
from config import MONGO_URI

async def main():
    print("\n" + "=" * 70)
    print("🔍 VERIFICADOR DE SESSÃO - MongoDB")
    print("=" * 70)
    
    # Conecta ao MongoDB
    db_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    session_collection = db_client["telegram_keyword_bot"]["session"]
    
    try:
        # Recupera documento de sessão
        doc = await session_collection.find_one({"_id": "session"})
        
        if not doc:
            print("\n❌ Nenhuma sessão encontrada no MongoDB!")
            print("   Execute: python setup_session.py")
            return
        
        print("\n✅ Sessão encontrada!")
        print("\nDocumento atual:")
        print("-" * 70)
        
        # Mostra informações
        for key, value in doc.items():
            if key == "value":
                # Não mostra a sessão inteira, é muito longa
                print(f"  {key}: {value[:50]}... (truncado)")
            elif isinstance(value, datetime):
                print(f"  {key}: {value.strftime('%d/%m/%Y %H:%M:%S')} UTC")
            else:
                print(f"  {key}: {value}")
        
        print("-" * 70)
        
        # Verifica timestamps
        has_created = "created_at" in doc
        has_updated = "updated_at" in doc
        
        print("\n📊 Status dos Timestamps:")
        print(f"  - created_at: {'✅ Presente' if has_created else '❌ Ausente'}")
        print(f"  - updated_at: {'✅ Presente' if has_updated else '❌ Ausente'}")
        
        # Migra se necessário
        if not has_created or not has_updated:
            print("\n🔧 Migração necessária...")
            now = datetime.now(timezone.utc)
            
            update_dict = {}
            if not has_created:
                update_dict["created_at"] = now
            if not has_updated:
                update_dict["updated_at"] = now
            
            await session_collection.update_one(
                {"_id": "session"},
                {"$set": update_dict}
            )
            
            print("✅ Timestamps adicionados com sucesso!")
            print(f"   - created_at: {now.strftime('%d/%m/%Y %H:%M:%S')} UTC")
            print(f"   - updated_at: {now.strftime('%d/%m/%Y %H:%M:%S')} UTC")
        else:
            print("\n✅ Documento já possui todos os timestamps!")
        
        # Info final
        print("\n" + "=" * 70)
        print("✨ Seu bot está pronto para rodar!")
        print("   Execute: python main.py")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Erro ao verificar sessão: {e}")
    finally:
        db_client.close()


if __name__ == "__main__":
    asyncio.run(main())
