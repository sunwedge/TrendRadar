#!/usr/bin/env python3
import os, ssl, smtplib, sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

def load_env_file(path: Path):
    if not path.exists():
        raise FileNotFoundError(path)
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            continue
        k, v = line.split('=', 1)
        k = k.strip()
        v = v.strip()
        # don't override real env
        os.environ.setdefault(k, v)

def newest_db(news_dir: Path) -> Path:
    dbs = sorted(news_dir.glob('*.db'), key=lambda p: p.stat().st_mtime, reverse=True)
    if not dbs:
        raise RuntimeError(f'No .db files in {news_dir}')
    return dbs[0]

def fetch_top10(db_path: Path):
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(
        """
        select n.rank, p.name as platform, n.title,
               case when n.url is not null and n.url != '' then n.url
                    when n.mobile_url is not null and n.mobile_url != '' then n.mobile_url
                    else '' end as url
        from news_items n
        join platforms p on p.id = n.platform_id
        order by n.rank asc
        limit 10
        """
    )
    rows = cur.fetchall()
    con.close()
    return rows

def send_email(subject: str, body: str):
    host = os.environ.get('EMAIL_SMTP_SERVER')
    port = int(os.environ.get('EMAIL_SMTP_PORT') or '465')
    user = os.environ.get('EMAIL_FROM')
    password = os.environ.get('EMAIL_PASSWORD')
    to = os.environ.get('EMAIL_TO')

    if not all([host, port, user, password, to]):
        missing = [k for k in ['EMAIL_SMTP_SERVER','EMAIL_SMTP_PORT','EMAIL_FROM','EMAIL_PASSWORD','EMAIL_TO'] if not os.environ.get(k)]
        raise RuntimeError('Missing env: ' + ','.join(missing))

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = user
    msg['To'] = to
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(host, port, context=context, timeout=30) as server:
        server.login(user, password)
        server.sendmail(user, [addr.strip() for addr in to.split(',') if addr.strip()], msg.as_string())


def main():
    repo = Path(__file__).resolve().parents[1]
    env_path = repo / 'docker' / '.env'
    load_env_file(env_path)

    db_path = newest_db(repo / 'output' / 'news')
    items = fetch_top10(db_path)

    lines = []
    lines.append(f"数据源: {db_path.name}")
    lines.append('')
    for i, r in enumerate(items, 1):
        lines.append(f"{i}. [{r['platform']}] {r['title']}")
        if r['url']:
            lines.append(f"   {r['url']}")
        lines.append('')

    subject = f"TrendRadar 热门资讯 Top10 ({db_path.stem})"
    body = "\n".join(lines).strip() + "\n"
    send_email(subject, body)
    print('OK: email sent')

if __name__ == '__main__':
    main()
