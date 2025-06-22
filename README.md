# Example n8n Workflow: Web Content Processing with AI

[English](#english) | [ไทย](#thai)

---

## English

### Overview
This n8n workflow automates the process of extracting important content from multiple web pages and processing it with AI assistance. The workflow is designed to scrape content from various positions (URLs), extract key information, and use AI to analyze and rearrange the content before sending it to Discord.

### Workflow Components

#### 1. Schedule Trigger
- **Function**: Initiates the workflow automatically
- **Configuration**: Set to run at specified intervals
- **Purpose**: Ensures regular content monitoring and processing

#### 2. Web Content Extraction (Positions 1-5)
Each position represents a different web source:
- **Pos 1-5**: HTTP Request nodes for different web pages
- **Find Importance**: Extracts key content from each page
- **HTML to MARK**: Converts HTML content to Markdown format

#### 3. Data Processing Pipeline
- **Merge**: Combines content from all 5 positions
- **Edit Fields**: Processes and formats the merged data
- **Code**: Custom JavaScript processing for data manipulation

#### 4. AI Integration
- **AI Agent**: Analyzes the processed content
- **Ollama Chat Model**: Provides AI-powered content analysis
- **Rearrange the message**: Reorganizes content based on AI insights

#### 5. Output Management
- **Loop Over Items**: Processes multiple items if needed
- **Discord**: Sends processed content to Discord channel
- **Replace Me**: Final processing step before output

### Setup Instructions

#### Prerequisites
- n8n instance (self-hosted or cloud)
- Discord webhook URL
- Ollama installation with chat model
- Target websites/URLs to monitor

#### Configuration Steps

1. **Schedule Trigger**
   ```
   Set your desired interval (e.g., every hour, daily)
   ```

2. **HTTP Request Nodes (Pos 1-5)**
   ```
   - URL: Enter your target website URLs
   - Method: GET
   - Headers: Add any required authentication or user-agent
   ```

3. **Content Extraction**
   ```
   Configure HTML parsing rules to extract important content
   Set up Markdown conversion parameters
   ```

4. **AI Configuration**
   ```
   - Ollama Model: Configure your preferred chat model
   - AI Agent: Set up content analysis prompts
   ```

5. **Discord Integration**
   ```
   - Webhook URL: Your Discord channel webhook
   - Message Format: Customize output format
   ```

### Features

- **Multi-Source Monitoring**: Tracks content from 5 different web sources
- **Intelligent Content Extraction**: Identifies important content automatically
- **AI-Powered Analysis**: Uses Ollama chat model for content insights
- **Automated Scheduling**: Runs on predefined intervals
- **Discord Integration**: Sends results directly to Discord channel
- **Error Handling**: Includes workflow execution management

### Use Cases

- **News Monitoring**: Track important news from multiple sources
- **Content Curation**: Automatically curate and summarize web content
- **Research Automation**: Monitor research papers or articles
- **Market Intelligence**: Track competitor websites or industry updates
- **Social Media Management**: Automated content discovery and sharing

### Workflow Logic

1. **Trigger**: Workflow starts on schedule
2. **Parallel Processing**: Simultaneously fetches content from 5 sources
3. **Content Extraction**: Identifies and extracts important information
4. **Format Conversion**: Converts HTML to Markdown for better processing
5. **Data Merging**: Combines all extracted content
6. **AI Analysis**: Processes content with AI for insights and organization
7. **Content Rearrangement**: Optimizes content structure and format
8. **Output**: Sends final processed content to Discord

### Customization Options

- **Source URLs**: Modify the 5 position URLs to monitor different websites
- **Extraction Rules**: Adjust content extraction criteria
- **AI Prompts**: Customize AI analysis instructions
- **Output Format**: Modify Discord message formatting
- **Schedule**: Adjust trigger timing based on your needs

### Troubleshooting

#### Common Issues
- **HTTP Request Failures**: Check URL accessibility and authentication
- **AI Model Errors**: Verify Ollama installation and model availability
- **Discord Webhook**: Ensure webhook URL is valid and channel permissions are set
- **Content Extraction**: Review HTML structure changes on target websites

#### Monitoring
- Check workflow execution history in n8n
- Monitor Discord channel for successful outputs
- Review error logs for failed executions

### Requirements

- n8n (latest version recommended)
- Ollama with chat model installed
- Discord server with webhook access
- Stable internet connection for web scraping

---

## Thai

### ภาพรวม
Workflow n8n นี้ทำหน้าที่ในการดึงเนื้อหาสำคัญจากหลายหน้าเว็บและประมวลผลด้วยความช่วยเหลือของ AI โดยได้รับการออกแบบมาเพื่อดึงข้อมูลจากตำแหน่งต่างๆ (URLs) สกัดข้อมูลสำคัญ และใช้ AI ในการวิเคราะห์และจัดเรียงเนื้อหาใหม่ก่อนส่งไปยัง Discord

### ส่วนประกอบของ Workflow

#### 1. Schedule Trigger (ตัวกำหนดเวลา)
- **หน้าที่**: เริ่มต้น workflow อัตโนมัติ
- **การตั้งค่า**: กำหนดให้ทำงานตามช่วงเวลาที่กำหนด
- **วัตถุประสงค์**: ตรวจสอบและประมวลผลเนื้อหาอย่างสม่ำเสมอ

#### 2. การดึงเนื้อหาเว็บ (ตำแหน่ง 1-5)
แต่ละตำแหน่งแทนแหล่งเว็บที่แตกต่างกัน:
- **Pos 1-5**: HTTP Request nodes สำหรับหน้าเว็บต่างๆ
- **Find Importance**: ดึงเนื้อหาสำคัญจากแต่ละหน้า
- **HTML to MARK**: แปลงเนื้อหา HTML เป็นรูปแบบ Markdown

#### 3. ขั้นตอนการประมวลผลข้อมูล
- **Merge**: รวมเนื้อหาจากทั้ง 5 ตำแหน่ง
- **Edit Fields**: ประมวลผลและจัดรูปแบบข้อมูลที่รวมแล้ว
- **Code**: การประมวลผล JavaScript แบบกำหนดเองสำหรับจัดการข้อมูล

#### 4. การรวม AI
- **AI Agent**: วิเคราะห์เนื้อหาที่ประมวลผลแล้ว
- **Ollama Chat Model**: ให้การวิเคราะห์เนื้อหาด้วยพลัง AI
- **Rearrange the message**: จัดระเบียบเนื้อหาใหม่ตามข้อมูลเชิงลึกจาก AI

#### 5. การจัดการผลลัพธ์
- **Loop Over Items**: ประมวลผลรายการหลายรายการหากจำเป็น
- **Discord**: ส่งเนื้อหาที่ประมวลผลแล้วไปยังช่อง Discord
- **Replace Me**: ขั้นตอนการประมวลผลสุดท้ายก่อนแสดงผล

### คำแนะนำการตั้งค่า

#### ข้อกำหนดเบื้องต้น
- n8n instance (self-hosted หรือ cloud)
- Discord webhook URL
- การติดตั้ง Ollama พร้อม chat model
- เว็บไซต์/URLs เป้าหมายที่ต้องการตรวจสอบ

#### ขั้นตอนการกำหนดค่า

1. **Schedule Trigger**
   ```
   กำหนดช่วงเวลาที่ต้องการ (เช่น ทุกชั่วโมง, รายวัน)
   ```

2. **HTTP Request Nodes (Pos 1-5)**
   ```
   - URL: ใส่ URLs ของเว็บไซต์เป้าหมายของคุณ
   - Method: GET
   - Headers: เพิ่ม authentication หรือ user-agent ที่จำเป็น
   ```

3. **การดึงเนื้อหา**
   ```
   กำหนดค่ากฎการ parse HTML เพื่อดึงเนื้อหาสำคัญ
   ตั้งค่าพารามิเตอร์การแปลง Markdown
   ```

4. **การกำหนดค่า AI**
   ```
   - Ollama Model: กำหนดค่า chat model ที่ต้องการ
   - AI Agent: ตั้งค่า prompts สำหรับการวิเคราะห์เนื้อหา
   ```

5. **การรวม Discord**
   ```
   - Webhook URL: webhook ของช่อง Discord ของคุณ
   - Message Format: ปรับแต่งรูปแบบการแสดงผล
   ```

### คุณสมบัติ

- **การตรวจสอบหลายแหล่ง**: ติดตามเนื้อหาจาก 5 แหล่งเว็บที่แตกต่างกัน
- **การดึงเนื้อหาอัจฉริยะ**: ระบุเนื้อหาสำคัญโดยอัตโนมัติ
- **การวิเคราะห์ด้วยพลัง AI**: ใช้ Ollama chat model สำหรับข้อมูลเชิงลึกของเนื้อหา
- **การจัดตารางเวลาอัตโนมัติ**: ทำงานตามช่วงเวลาที่กำหนดไว้ล่วงหน้า
- **การรวม Discord**: ส่งผลลัพธ์โดยตรงไปยังช่อง Discord
- **การจัดการข้อผิดพลาด**: รวมการจัดการการดำเนินการ workflow

### กรณีการใช้งาน

- **การตรวจสอบข่าว**: ติดตามข่าวสำคัญจากหลายแหล่ง
- **การคัดสรรเนื้อหา**: คัดสรรและสรุปเนื้อหาเว็บโดยอัตโนมัติ
- **การทำงานวิจัยอัตโนมัติ**: ตรวจสอบเอกสารงานวิจัยหรือบทความ
- **ข่าวกรองตลาด**: ติดตามเว็บไซต์คู่แข่งหรือการอัปเดตในอุตสาหกรรม
- **การจัดการโซเชียลมีเดีย**: การค้นหาและแบ่งปันเนื้อหาอัตโนมัติ

### ตรรกะของ Workflow

1. **Trigger**: Workflow เริ่มต้นตามตารางเวลา
2. **การประมวลผลแบบขนาน**: ดึงเนื้อหาจาก 5 แหล่งพร้อมกัน
3. **การดึงเนื้อหา**: ระบุและดึงข้อมูลสำคัญ
4. **การแปลงรูปแบบ**: แปลง HTML เป็น Markdown เพื่อการประมวลผลที่ดีกว่า
5. **การรวมข้อมูล**: รวมเนื้อหาที่ดึงมาทั้งหมด
6. **การวิเคราะห์ AI**: ประมวลผลเนื้อหาด้วย AI เพื่อข้อมูลเชิงลึกและการจัดระเบียบ
7. **การจัดเรียงเนื้อหาใหม่**: ปรับปรุงโครงสร้างและรูปแบบเนื้อหา
8. **การแสดงผล**: ส่งเนื้อหาที่ประมวลผลสุดท้ายไปยัง Discord

### ตัวเลือกการปรับแต่ง

- **URLs แหล่งที่มา**: แก้ไข URLs ของ 5 ตำแหน่งเพื่อตรวจสอบเว็บไซต์ที่แตกต่างกัน
- **กฎการดึงข้อมูล**: ปรับเกณฑ์การดึงเนื้อหา
- **AI Prompts**: ปรับแต่งคำสั่งการวิเคราะห์ AI
- **รูปแบบการแสดงผล**: แก้ไขการจัดรูปแบบข้อความ Discord
- **ตารางเวลา**: ปรับเวลา trigger ตามความต้องการของคุณ

### การแก้ไขปัญหา

#### ปัญหาทั่วไป
- **ความล้มเหลวของ HTTP Request**: ตรวจสอบการเข้าถึง URL และการรับรองความถูกต้อง
- **ข้อผิดพลาดของ AI Model**: ตรวจสอบการติดตั้ง Ollama และความพร้อมใช้งานของ model
- **Discord Webhook**: ตรวจสอบให้แน่ใจว่า webhook URL ถูกต้องและการอนุญาตช่องได้รับการตั้งค่า
- **การดึงเนื้อหา**: ตรวจสอบการเปลี่ยนแปลงโครงสร้าง HTML บนเว็บไซต์เป้าหมาย

#### การตรวจสอบ
- ตรวจสอบประวัติการดำเนินการ workflow ใน n8n
- ตรวจสอบช่อง Discord สำหรับผลลัพธ์ที่สำเร็จ
- ตรวจสอบ error logs สำหรับการดำเนินการที่ล้มเหลว

### ข้อกำหนด

- n8n (แนะนำเวอร์ชันล่าสุด)
- Ollama พร้อม chat model ที่ติดตั้งแล้ว
- เซิร์ฟเวอร์ Discord พร้อมการเข้าถึง webhook
- การเชื่อมต่ออินเทอร์เน็ตที่เสถียรสำหรับการ scraping เว็บ

### ใบอนุญาต
Workflow นี้มีให้เป็นไปตามสภาพสำหรับวัตถุประสงค์ทางการศึกษาและระบบอัตโนมัติ

### การสนับสนุน
สามารถแก้ไขและปรับปรุง workflow นี้ตามความต้องการเฉพาะของคุณได้ กรุณาพิจารณาแบ่งปันการปรับปรุงกับชุมชน n8n

---

*หมายเหตุ: โปรดจำไว้ว่าต้องเคารพข้อกำหนดการให้บริการของเว็บไซต์และใช้การจำกัดอัตราที่เหมาะสมเมื่อทำการ scraping เนื้อหา*
