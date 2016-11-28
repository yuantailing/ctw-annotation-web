from django.shortcuts import render
from django.http import HttpResponse, StreamingHttpResponse, Http404

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from . import filename_mapper
import zipfile
import os
import io

# Create your views here.
@login_required
def index(request):
    return render(request, 'collection/index.html', {})

def test(request):
    def zip_iterator(file_list, compression=zipfile.ZIP_STORED):
        buffer = io.BytesIO()
        zf = zipfile.ZipFile(buffer, mode='w', compression=compression, allowZip64=False)
        last_write = buffer.tell()
        for tup in file_list:
            zf.write(*tup)
            current = buffer.tell()
            buffer.seek(last_write, 0)
            yield buffer.read(current - last_write)
            last_write = current
        zf.close()
        current = buffer.tell()
        if current != last_write:
            buffer.seek(last_write, 0)
            yield buffer.read(current - last_write)
        buffer.close()
    direction = 1
    new_names = ['000016', '000017', '000019', '000020']
    file_list = []
    for new_name in new_names:
        old_name = filename_mapper.mapper.new2old[new_name]
        file_list.append(('Z:/tiger/1_part/%s.%d.jpg' % (old_name, direction), '%d%s.jpg' % (direction, new_name)))
    response = StreamingHttpResponse(zip_iterator(file_list))
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="task_distributed.zip"'
    for filename in file_list:
        if not os.path.exists(filename[0]):
            raise ValueError("File not found. It may be a server filesystem issue. Please report this incident to administratior.")
    return response
