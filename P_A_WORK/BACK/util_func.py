import aiofiles

async def save_file(in_file, out_file_path: str):
    async with aiofiles.open(out_file_path, 'wb') as out_file:
            while content := await in_file.read(1024):  # async read chunk
                await out_file.write(content)  # async write chunk
                
                
                
def get_err_dict(error_type: str, error_message: str):
    return {"result": False,
            "error_type": error_type,
            "error_message": error_message,
            }