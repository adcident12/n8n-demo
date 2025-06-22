from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
import json
from urllib.parse import urljoin
import logging
import uuid
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor
import os

# ตั้งค่า logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# สร้าง FastAPI app
app = FastAPI(
    title="Web Scraper API",
    description="API สำหรับ scrape หน้าเว็บทั้งแบบ static และ JavaScript",
    version="1.0.0"
)

# เพิ่ม CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global storage สำหรับ async tasks
task_storage = {}

# Pydantic models
class ScrapeRequest(BaseModel):
    url: HttpUrl
    method: Optional[str] = Field(default="auto", description="static, javascript, หรือ auto")
    wait_for_element: Optional[str] = Field(default=None, description="CSS selector ของ element ที่รอ")
    wait_time: Optional[int] = Field(default=3, description="เวลารอเพิ่มเติม (วินาที)")
    include_html: Optional[bool] = Field(default=False, description="รวม HTML ดิบหรือไม่")
    include_images: Optional[bool] = Field(default=True, description="รวมข้อมูล images หรือไม่")
    include_links: Optional[bool] = Field(default=True, description="รวมข้อมูล links หรือไม่")

class MultipleScrapeRequest(BaseModel):
    urls: List[HttpUrl]
    method: Optional[str] = Field(default="auto", description="static, javascript, หรือ auto")
    wait_for_element: Optional[str] = Field(default=None, description="CSS selector ของ element ที่รอ")
    wait_time: Optional[int] = Field(default=3, description="เวลารอเพิ่มเติม (วินาที)")
    delay: Optional[int] = Field(default=1, description="เวลาพักระหว่าง URLs (วินาที)")
    include_html: Optional[bool] = Field(default=False, description="รวม HTML ดิบหรือไม่")
    include_images: Optional[bool] = Field(default=True, description="รวมข้อมูล images หรือไม่")
    include_links: Optional[bool] = Field(default=True, description="รวมข้อมูล links หรือไม่")

class ScrapeResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    method_used: Optional[str] = None
    timestamp: str
    processing_time: Optional[float] = None

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str  # pending, running, completed, failed
    progress: Optional[int] = None
    total: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None

class AsyncWebScraper:
    def __init__(self, headless=True, timeout=15):
        self.timeout = timeout
        self.headless = headless
        self.executor = ThreadPoolExecutor(max_workers=3)
        
    async def scrape_static_async(self, url: str, include_html=False, include_images=True, include_links=True):
        """Async static scraping"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}")
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # ดึงข้อมูลพื้นฐาน
                    data = {
                        'url': url,
                        'status_code': response.status,
                        'title': soup.title.string if soup.title else '',
                        'meta_description': '',
                        'headings': {},
                        'text_content': soup.get_text(strip=True),
                        'content_length': len(soup.get_text(strip=True))
                    }
                    
                    # Meta description
                    meta_desc = soup.find('meta', attrs={'name': 'description'})
                    if meta_desc:
                        data['meta_description'] = meta_desc.get('content', '')
                    
                    # Headings
                    for i in range(1, 7):
                        headings = soup.find_all(f'h{i}')
                        data['headings'][f'h{i}'] = [h.get_text(strip=True) for h in headings]
                    
                    # Links
                    if include_links:
                        data['links'] = []
                        for link in soup.find_all('a', href=True):
                            data['links'].append({
                                'text': link.get_text(strip=True),
                                'href': urljoin(url, link['href'])
                            })
                    
                    # Images
                    if include_images:
                        data['images'] = []
                        for img in soup.find_all('img'):
                            data['images'].append({
                                'alt': img.get('alt', ''),
                                'src': urljoin(url, img.get('src', '')) if img.get('src') else '',
                                'title': img.get('title', '')
                            })
                    
                    # HTML
                    if include_html:
                        data['html'] = str(soup)
                    
                    return data
                    
        except Exception as e:
            raise Exception(f"Static scraping failed: {str(e)}")
    
    def scrape_javascript_sync(self, url: str, wait_for_element=None, wait_time=3, 
                             include_html=False, include_images=True, include_links=True):
        """Synchronous JavaScript scraping (to run in thread)"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        driver = None
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(self.timeout)
            driver.get(url)
            
            # รอ element ถ้าระบุ
            if wait_for_element:
                try:
                    WebDriverWait(driver, self.timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_element))
                    )
                except TimeoutException:
                    logger.warning(f"Timeout waiting for element: {wait_for_element}")
            
            # รอเพิ่มเติม
            time.sleep(wait_time)
            
            # ดึงข้อมูล
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            data = {
                'url': url,
                'title': driver.title,
                'current_url': driver.current_url,
                'meta_description': '',
                'headings': {},
                'text_content': soup.get_text(strip=True),
                'content_length': len(soup.get_text(strip=True))
            }
            
            # Meta description
            try:
                meta_desc = driver.find_element(By.CSS_SELECTOR, 'meta[name="description"]')
                data['meta_description'] = meta_desc.get_attribute('content') or ''
            except:
                pass
            
            # Headings
            for i in range(1, 7):
                try:
                    headings = driver.find_elements(By.TAG_NAME, f'h{i}')
                    data['headings'][f'h{i}'] = [h.text.strip() for h in headings]
                except:
                    data['headings'][f'h{i}'] = []
            
            # Links
            if include_links:
                data['links'] = []
                try:
                    links = driver.find_elements(By.TAG_NAME, 'a')
                    for link in links:
                        href = link.get_attribute('href')
                        if href:
                            data['links'].append({
                                'text': link.text.strip(),
                                'href': href
                            })
                except:
                    pass
            
            # Images
            if include_images:
                data['images'] = []
                try:
                    images = driver.find_elements(By.TAG_NAME, 'img')
                    for img in images:
                        src = img.get_attribute('src')
                        if src:
                            data['images'].append({
                                'alt': img.get_attribute('alt') or '',
                                'src': src,
                                'title': img.get_attribute('title') or ''
                            })
                except:
                    pass
            
            # HTML
            if include_html:
                data['html'] = html
            
            return data
            
        except Exception as e:
            raise Exception(f"JavaScript scraping failed: {str(e)}")
        finally:
            if driver:
                driver.quit()
    
    async def scrape_javascript_async(self, url: str, **kwargs):
        """Async wrapper for JavaScript scraping"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self.scrape_javascript_sync, 
            url, 
            kwargs.get('wait_for_element'),
            kwargs.get('wait_time', 3),
            kwargs.get('include_html', False),
            kwargs.get('include_images', True),
            kwargs.get('include_links', True)
        )
    
    async def auto_scrape_async(self, url: str, **kwargs):
        """Auto-detect scraping method"""
        try:
            # ลอง static ก่อน
            static_data = await self.scrape_static_async(url, **kwargs)
            
            # ถ้าได้ข้อมูลเยอะพอ ใช้ static
            if static_data.get('content_length', 0) > 100:
                static_data['method'] = 'static'
                return static_data
            
            # ถ้าไม่ได้ผล ลอง JavaScript
            logger.info(f"Static insufficient for {url}, trying JavaScript")
            
        except Exception as e:
            logger.warning(f"Static scraping failed for {url}: {e}")
        
        # ใช้ JavaScript method
        js_data = await self.scrape_javascript_async(url, **kwargs)
        js_data['method'] = 'javascript'
        return js_data

# สร้าง scraper instance
scraper = AsyncWebScraper()

@app.get("/")
async def root():
    return {
        "message": "Web Scraper API",
        "version": "1.0.0",
        "endpoints": {
            "scrape": "/scrape - POST - Scrape single URL",
            "scrape/multiple": "/scrape/multiple - POST - Scrape multiple URLs",
            "scrape/async": "/scrape/async - POST - Async scrape multiple URLs",
            "task/status": "/task/{task_id} - GET - Check task status",
            "health": "/health - GET - Health check"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_single(request: ScrapeRequest):
    """Scrape single URL"""
    start_time = time.time()
    
    try:
        url = str(request.url)
        kwargs = {
            'wait_for_element': request.wait_for_element,
            'wait_time': request.wait_time,
            'include_html': request.include_html,
            'include_images': request.include_images,
            'include_links': request.include_links
        }
        
        if request.method == 'static':
            data = await scraper.scrape_static_async(url, **kwargs)
            method_used = 'static'
        elif request.method == 'javascript':
            data = await scraper.scrape_javascript_async(url, **kwargs)
            method_used = 'javascript'
        else:  # auto
            data = await scraper.auto_scrape_async(url, **kwargs)
            method_used = data.get('method', 'auto')
        
        processing_time = time.time() - start_time
        
        return ScrapeResponse(
            success=True,
            data=data,
            method_used=method_used,
            timestamp=datetime.now().isoformat(),
            processing_time=round(processing_time, 2)
        )
        
    except Exception as e:
        logger.error(f"Scraping error: {e}")
        return ScrapeResponse(
            success=False,
            error=str(e),
            timestamp=datetime.now().isoformat(),
            processing_time=round(time.time() - start_time, 2)
        )

@app.post("/scrape/multiple", response_model=List[ScrapeResponse])
async def scrape_multiple(request: MultipleScrapeRequest):
    """Scrape multiple URLs synchronously"""
    results = []
    
    for i, url in enumerate(request.urls):
        start_time = time.time()
        
        try:
            url_str = str(url)
            kwargs = {
                'wait_for_element': request.wait_for_element,
                'wait_time': request.wait_time,
                'include_html': request.include_html,
                'include_images': request.include_images,
                'include_links': request.include_links
            }
            
            if request.method == 'static':
                data = await scraper.scrape_static_async(url_str, **kwargs)
                method_used = 'static'
            elif request.method == 'javascript':
                data = await scraper.scrape_javascript_async(url_str, **kwargs)
                method_used = 'javascript'
            else:  # auto
                data = await scraper.auto_scrape_async(url_str, **kwargs)
                method_used = data.get('method', 'auto')
            
            processing_time = time.time() - start_time
            
            results.append(ScrapeResponse(
                success=True,
                data=data,
                method_used=method_used,
                timestamp=datetime.now().isoformat(),
                processing_time=round(processing_time, 2)
            ))
            
        except Exception as e:
            logger.error(f"Scraping error for {url}: {e}")
            results.append(ScrapeResponse(
                success=False,
                error=str(e),
                timestamp=datetime.now().isoformat(),
                processing_time=round(time.time() - start_time, 2)
            ))
        
        # พักระหว่าง URLs
        if i < len(request.urls) - 1 and request.delay > 0:
            await asyncio.sleep(request.delay)
    
    return results

@app.post("/scrape/async")
async def scrape_multiple_async(request: MultipleScrapeRequest, background_tasks: BackgroundTasks):
    """Scrape multiple URLs asynchronously"""
    task_id = str(uuid.uuid4())
    
    # สร้าง task info
    task_info = {
        'task_id': task_id,
        'status': 'pending',
        'progress': 0,
        'total': len(request.urls),
        'result': None,
        'error': None,
        'created_at': datetime.now().isoformat(),
        'completed_at': None
    }
    
    task_storage[task_id] = task_info
    
    # เริ่ม background task
    background_tasks.add_task(process_multiple_urls, task_id, request)
    
    return {"task_id": task_id, "status": "queued", "total_urls": len(request.urls)}

async def process_multiple_urls(task_id: str, request: MultipleScrapeRequest):
    """Process multiple URLs in background"""
    try:
        task_storage[task_id]['status'] = 'running'
        results = []
        
        for i, url in enumerate(request.urls):
            start_time = time.time()
            
            try:
                url_str = str(url)
                kwargs = {
                    'wait_for_element': request.wait_for_element,
                    'wait_time': request.wait_time,
                    'include_html': request.include_html,
                    'include_images': request.include_images,
                    'include_links': request.include_links
                }
                
                if request.method == 'static':
                    data = await scraper.scrape_static_async(url_str, **kwargs)
                    method_used = 'static'
                elif request.method == 'javascript':
                    data = await scraper.scrape_javascript_async(url_str, **kwargs)
                    method_used = 'javascript'
                else:  # auto
                    data = await scraper.auto_scrape_async(url_str, **kwargs)
                    method_used = data.get('method', 'auto')
                
                processing_time = time.time() - start_time
                
                results.append({
                    'success': True,
                    'data': data,
                    'method_used': method_used,
                    'timestamp': datetime.now().isoformat(),
                    'processing_time': round(processing_time, 2)
                })
                
            except Exception as e:
                results.append({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat(),
                    'processing_time': round(time.time() - start_time, 2)
                })
            
            # อัปเดต progress
            task_storage[task_id]['progress'] = i + 1
            
            # พักระหว่าง URLs
            if i < len(request.urls) - 1 and request.delay > 0:
                await asyncio.sleep(request.delay)
        
        # เสร็จสิ้น
        task_storage[task_id]['status'] = 'completed'
        task_storage[task_id]['result'] = results
        task_storage[task_id]['completed_at'] = datetime.now().isoformat()
        
    except Exception as e:
        task_storage[task_id]['status'] = 'failed'
        task_storage[task_id]['error'] = str(e)
        task_storage[task_id]['completed_at'] = datetime.now().isoformat()

@app.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Check task status"""
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_info = task_storage[task_id]
    
    return TaskStatusResponse(
        task_id=task_id,
        status=task_info['status'],
        progress=task_info['progress'],
        total=task_info['total'],
        result=task_info['result'],
        error=task_info['error'],
        created_at=task_info['created_at'],
        completed_at=task_info['completed_at']
    )

@app.delete("/task/{task_id}")
async def delete_task(task_id: str):
    """Delete task from storage"""
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    
    del task_storage[task_id]
    return {"message": "Task deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7890)