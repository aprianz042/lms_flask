import random
import string

from werkzeug.utils import secure_filename
from datetime import datetime

def generate_filename(extension):
    random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    now = datetime.now()
    timestamp = now.strftime("%d%m%Y_%H%M%S")  # Format: tanggal_bulan_tahun_jam_menit_detik
    filename = f"IPDN_{random_string}_{timestamp}.{extension}"
    return filename