
from sqlalchemy import text
from app.db.postgres import SessionLocal

def fix_password():
    db = SessionLocal()
    try:
        # 正确的哈希值，注意这里是 Python 字符串，不需要 shell 转义
        # hash for "12345678"
        new_hash = "$2b$12$LqEwXlcLqkKqGKLVWEPc7.9eyqZMEhyMl.LP0n3XgbPsw.13uE8ja"
        username = "Radinat"
        
        sql = text("UPDATE users SET hashed_password = :h WHERE username = :u")
        result = db.execute(sql, {"h": new_hash, "u": username})
        db.commit()
        print(f"Password updated for user {username}. Rows affected: {result.rowcount}")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_password()
