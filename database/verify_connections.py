"""
数据库连接验证脚本
用于验证 PostgreSQL、Neo4j 和 Redis 的连接
"""

import sys
import os

# 添加父目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def verify_postgres():
    """验证 PostgreSQL 连接"""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor

        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="radiant",
            user="postgres",
            password="Radiant_Postgres_2026!"
        )

        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
        tables = cursor.fetchall()

        print("✅ PostgreSQL 连接成功！")
        print(f"   找到 {len(tables)} 个表:")
        for table in tables:
            print(f"   - {table['tablename']}")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ PostgreSQL 连接失败: {e}")
        return False


def verify_neo4j():
    """验证 Neo4j 连接"""
    try:
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "Radiant_Neo4j_2026!")
        )

        with driver.session() as session:
            # 查询节点统计
            result = session.run("MATCH (n) RETURN labels(n) as type, count(n) as count")
            stats = list(result)

            # 查询索引
            result = session.run("SHOW INDEXES")
            indexes = list(result)

            print("✅ Neo4j 连接成功！")
            print(f"   节点统计:")
            for record in stats:
                print(f"   - {record['type'][0]}: {record['count']} 个节点")
            print(f"   共 {len(indexes)} 个索引")

        driver.close()
        return True

    except Exception as e:
        print(f"❌ Neo4j 连接失败: {e}")
        return False


def verify_redis():
    """验证 Redis 连接"""
    try:
        import redis

        client = redis.Redis(
            host="localhost",
            port=6379,
            db=0,
            decode_responses=True
        )

        # 测试 ping
        response = client.ping()

        # 测试写入和读取
        client.set("test_key", "test_value", ex=10)
        value = client.get("test_key")

        print("✅ Redis 连接成功！")
        print(f"   Ping 响应: {response}")
        print(f"   测试读写: OK")

        client.close()
        return True

    except Exception as e:
        print(f"❌ Redis 连接失败: {e}")
        return False


def main():
    print("=" * 60)
    print("Radiant 项目数据库连接验证")
    print("=" * 60)
    print()

    results = {
        "PostgreSQL": verify_postgres(),
        "Neo4j": verify_neo4j(),
        "Redis": verify_redis()
    }

    print()
    print("=" * 60)
    print("验证结果汇总")
    print("=" * 60)

    all_success = all(results.values())

    for db, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{db:20s}: {status}")

    print()

    if all_success:
        print("🎉 所有数据库连接验证成功！项目数据库已准备就绪。")
        return 0
    else:
        print("⚠️  部分数据库连接失败，请检查配置和服务状态。")
        print()
        print("检查建议:")
        print("1. 确认 Docker 容器正在运行: docker ps")
        print("2. 检查环境变量配置: .env 文件")
        print("3. 查看容器日志: docker logs <container-name>")
        return 1


if __name__ == "__main__":
    # 检查依赖
    required_packages = ["psycopg2", "neo4j", "redis"]
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("⚠️  缺少必要的 Python 包，请安装:")
        print(f"   pip install {' '.join(missing_packages)}")
        sys.exit(1)

    sys.exit(main())
