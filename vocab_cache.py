"""
MongoDB cache functions cho vocab info
"""
from datetime import datetime
from typing import Optional, Dict, Any
import os
import pymongo


CACHE_COLLECTION = "vocab_cache"
# Database name: ưu tiên environment variable, nếu không có thì dùng "vocab" làm mặc định
DATABASE_NAME = os.getenv("MONGODB_DATABASE_NAME", "vocab")
_db_instance = None


def _get_db():
    """
    Lazy load db instance để tránh connection timeout khi import
    
    Returns:
        db instance hoặc None nếu không thể kết nối
    """
    global _db_instance
    if _db_instance is not None:
        return _db_instance
    
    try:
        from agno_agent import db
        _db_instance = db
        return db
    except Exception as e:
        print(f"Warning: Cannot import db from agno_agent: {e}")
        return None


def _get_collection():
    """
    Lấy MongoDB collection từ db instance
    
    Returns:
        MongoDB collection hoặc None nếu không thể truy cập
    """
    try:
        db = _get_db()
        if db is None:
            return None
        
        # MongoDb từ agno có db_client attribute
        if hasattr(db, 'db_client'):
            client = db.db_client
            # Lấy database "vocab" từ client
            database = client.get_database(DATABASE_NAME)
            collection = database[CACHE_COLLECTION]
            return collection
        
        # Fallback: thử các cách khác nếu db_client không có
        if hasattr(db, 'client'):
            client = db.client
            if isinstance(client, pymongo.MongoClient):
                database = client.get_database(DATABASE_NAME)
                collection = database[CACHE_COLLECTION]
                return collection
        
        # Nếu có database attribute nhưng cần database khác
        if hasattr(db, 'database'):
            db_instance = db.database
            if isinstance(db_instance, pymongo.database.Database):
                # Lấy client từ database instance và tạo database mới
                client = db_instance.client
                database = client.get_database(DATABASE_NAME)
                collection = database[CACHE_COLLECTION]
                return collection
        
        # Nếu có _get_collection method, có thể dùng nhưng cần chỉ định database
        # Tuy nhiên method này có thể chỉ dùng database mặc định
        # Nên tốt nhất là dùng db_client trực tiếp
        
        return None
    except (pymongo.errors.ServerSelectionTimeoutError, 
            pymongo.errors.NetworkTimeout,
            ConnectionError,
            TimeoutError) as e:
        print(f"Warning: MongoDB connection timeout/error: {e}")
        return None
    except Exception as e:
        print(f"Warning: Error getting collection: {e}")
        import traceback
        traceback.print_exc()
        return None


def _generate_cache_key(vocab: str, language: str) -> str:
    """
    Tạo cache key từ vocab và language
    
    Args:
        vocab: Từ vựng
        language: Ngôn ngữ
        
    Returns:
        Cache key dạng: vocab_lowercase_language
    """
    vocab_normalized = vocab.lower().strip()
    language_normalized = language.lower().strip()
    return f"{vocab_normalized}_{language_normalized}"


def get_cached_vocab_info(vocab: str, language: str) -> Optional[Dict[str, Any]]:
    """
    Lấy thông tin từ vựng từ cache
    
    Args:
        vocab: Từ vựng cần tra cứu
        language: Ngôn ngữ
        
    Returns:
        Cached data nếu tồn tại, None nếu không
    """
    try:
        collection = _get_collection()
        if collection is None:
            return None
            
        cache_key = _generate_cache_key(vocab, language)
        # Set timeout ngắn để tránh block quá lâu
        cached_doc = collection.find_one({"_id": cache_key}, max_time_ms=5000)
        
        if cached_doc and "data" in cached_doc:
            return cached_doc["data"]
        
        return None
    except (pymongo.errors.ServerSelectionTimeoutError,
            pymongo.errors.NetworkTimeout,
            ConnectionError,
            TimeoutError) as e:
        # Nếu có lỗi timeout, log và trả về None để fallback sang LLM
        print(f"Warning: MongoDB timeout when getting cache: {e}")
        return None
    except Exception as e:
        # Nếu có lỗi khi query cache, log và trả về None để fallback sang LLM
        print(f"Warning: Error getting cache: {e}")
        return None


def save_vocab_info_to_cache(vocab: str, language: str, data: Dict[str, Any]) -> None:
    """
    Lưu thông tin từ vựng vào cache
    
    Args:
        vocab: Từ vựng
        language: Ngôn ngữ
        data: Dữ liệu cần cache (full response data)
    """
    try:
        collection = _get_collection()
        if collection is None:
            return
        
        cache_key = _generate_cache_key(vocab, language)
        now = datetime.utcnow()
        
        document = {
            "_id": cache_key,
            "vocab": vocab,
            "language": language,
            "data": data,
            "updated_at": now
        }
        
        # Kiểm tra xem document đã tồn tại chưa với timeout ngắn
        existing = collection.find_one({"_id": cache_key}, max_time_ms=5000)
        if existing:
            # Update existing document
            document["created_at"] = existing.get("created_at", now)
            collection.update_one(
                {"_id": cache_key},
                {"$set": document}
            )
        else:
            # Insert new document
            document["created_at"] = now
            collection.insert_one(document)
            
    except (pymongo.errors.ServerSelectionTimeoutError,
            pymongo.errors.NetworkTimeout,
            ConnectionError,
            TimeoutError) as e:
        # Nếu có lỗi timeout, log nhưng không throw để không ảnh hưởng đến response
        print(f"Warning: MongoDB timeout when saving cache: {e}")
    except Exception as e:
        # Nếu có lỗi khi save cache, log nhưng không throw để không ảnh hưởng đến response
        print(f"Warning: Error saving cache: {e}")
