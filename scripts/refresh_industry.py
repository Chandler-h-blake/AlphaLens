"""Run with PYTHONPATH=backend python scripts/refresh_industry.py."""
from app.services.industry_refresh import refresh_rotation

if __name__ == '__main__':
    refresh_rotation()
    print('行业快照已更新')
