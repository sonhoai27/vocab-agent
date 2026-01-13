"""
MongoDB cache functions cho vocab info
"""
from datetime import datetime
from typing import Optional, Dict, Any
import pymongo


CACHE_COLLECTION = "vocab_cache"
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
            
        # Thử các cách truy cập collection
        if hasattr(db, 'client'):
            # Nếu db có client attribute (pymongo client)
            database = db.client.get_database()
            return database[CACHE_COLLECTION]
        elif hasattr(db, 'db'):
            # Nếu db có db attribute
            return db.db[CACHE_COLLECTION]
        elif hasattr(db, 'get_collection'):
            # Nếu db có method get_collection
            return db.get_collection(CACHE_COLLECTION)
        elif isinstance(db, pymongo.database.Database):
            # Nếu db là Database instance
            return db[CACHE_COLLECTION]
        else:
            # Fallback: thử truy cập như dictionary
            return db[CACHE_COLLECTION] if hasattr(db, '__getitem__') else None
    except (pymongo.errors.ServerSelectionTimeoutError, 
            pymongo.errors.NetworkTimeout,
            ConnectionError,
            TimeoutError) as e:
        print(f"Warning: MongoDB connection timeout/error: {e}")
        return None
    except Exception as e:
        print(f"Warning: Error getting collection: {e}")
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
                {"$set": document},
                max_time_ms=5000
            )
        else:
            # Insert new document
            document["created_at"] = now
            collection.insert_one(document, max_time_ms=5000)
            
    except (pymongo.errors.ServerSelectionTimeoutError,
            pymongo.errors.NetworkTimeout,
            ConnectionError,
            TimeoutError) as e:
        # Nếu có lỗi timeout, log nhưng không throw để không ảnh hưởng đến response
        print(f"Warning: MongoDB timeout when saving cache: {e}")
    except Exception as e:
        # Nếu có lỗi khi save cache, log nhưng không throw để không ảnh hưởng đến response
        print(f"Warning: Error saving cache: {e}")
