from pydantic import BaseModel, ConfigDict, Field

from typing import List, Optional




class ResultOut(BaseModel):
    result: bool
    
class ErrResultOut(ResultOut):
    error_type: str
    error_message: str
    
    
    
class TweetResultOut(ResultOut):
    tweet_id: int

class MediaResultOut(ResultOut):
    media_id: int
   

# USERS

class ShortUser(BaseModel):
    id: int
    name: str
    
class UserModel(ShortUser):
    followers: List[ShortUser]
    following: List[ShortUser]

    model_config = ConfigDict(from_attributes=True)


class UserResultOut(ResultOut):
    user: UserModel
    

# TWEETS

class TweetIn(BaseModel):
    """ 
    """
    tweet_data: str
    tweet_media_ids: Optional[List[int]] = None

class PictureOut(BaseModel):
    ...

class TweetOut(BaseModel): #TweetIn):
    """
    """
    content: str
    # не очень понял, что за список, каким образом он передается фронтУ.
    attachments: Optional[List[str]] = None
    
    id: int
    author: ShortUser
    likes: Optional[List[ShortUser]] = None
    
    
    model_config = ConfigDict(from_attributes=True)
    
    
class TweetResultListOut(ResultOut):
    tweets: List[TweetOut] = None


