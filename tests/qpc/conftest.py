import io
import json
import tarfile


def create_tar_buffer(files_data, encoding="utf-8", meta_encoding="utf-8"):
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar_file:
        for file_name, file_content in files_data.items():
            if "metadata.json" in file_name:
                file_bytes = json.dumps(file_content).encode(meta_encoding)
            elif file_name.endswith("json"):
                file_bytes = json.dumps(file_content).encode(encoding)
            else:
                return None
            info = tarfile.TarInfo(name=file_name)
            info.size = len(file_bytes)
            tar_file.addfile(tarinfo=info, fileobj=io.BytesIO(file_bytes))
    tar_buffer.seek(0)
    return tar_buffer.getvalue()
