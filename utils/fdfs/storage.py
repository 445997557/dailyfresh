from django.core.files.storage import FileSystemStorage
from fdfs_client.client import Fdfs_client


class FdfsStorage(FileSystemStorage):
    def _save(self, name, content):
        # path = super()._save(name, content)
        client = Fdfs_client('utils/fdfs/client.conf')
        try:
            date = content.read()
            result = client.upload_by_buffer(date)
            status = result.get('Status')
            if status == 'Upload successed.':
                path = result.get('Remote file_id')
            else:
                raise Exception('上传失败')
        except Exception as e:
            raise e
        return path

    def url(self, name):
        path = 'http://127.0.0.1:8888/' + super().url(name)
        return path


