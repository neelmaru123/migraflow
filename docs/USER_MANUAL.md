# Migraflow User Manual

### A Simple, Step-by-Step Guide to Moving and Merging Your Data

---

## Welcome to Migraflow!

Moving business data from old systems into a new system used to require weeks of manual spreadsheet work, complex scripts, and technical headaches. **Migraflow** simplifies this entire process into a friendly, guided experience powered by smart AI assistance.

Think of Migraflow like a **professional moving service** for your business records:

1. It takes an inventory of what you have in your old systems.
2. It organizes everything neatly into boxes labeled for your new system.
3. It lets you review the plan, make changes in plain English, and confirms everything is ready.
4. It moves everything across smoothly and keeps you updated every step of the way.

---

> [!NOTE]
>
> ### 🔒 The Migraflow Privacy Guarantee
>
> **Your actual business data and customer records never leave your own secure servers.**
> Migraflow only looks at the _labels_ of your data (such as table names, column names, and formats) to plan the move. The actual data transfer happens entirely inside your company's own protected network.

---

## 1. Quick Tour: Understanding Your Screen

When you log into Migraflow, you will see a clean, modern dashboard. Here are the main sections you will use:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  MIGRAFLOW       [ Dashboard ]   [ Data Sources ]   [ Plans ]   [ Execution ]│
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Active Projects              System Health              Total Records     │
│       3 Running                   ● All Connected             1.2M Migrated │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ 1. Connect Sources  ──►  2. Review Data  ──►  3. AI Plan  ──► 4. Move │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Color Status Guide

Whenever you see a badge or indicator on your screen, here is what the colors mean:

| Indicator Color                      | Meaning                                                  | What You Should Do                                   |
| :----------------------------------- | :------------------------------------------------------- | :--------------------------------------------------- |
| 🟢 **Green (Online / Ready)**        | Everything is working perfectly.                         | Proceed to the next step.                            |
| 🟡 **Yellow (In Progress / Review)** | The system is analyzing or moving data.                  | Wait a moment or review the suggested changes.       |
| 🔴 **Red (Action Needed)**           | A connection was interrupted or a field needs attention. | Check the helpful alert message displayed on screen. |

---

## 2. Step 1: Connecting Your Systems

Before Migraflow can help you organize your data, it needs to know where your information is coming from (**Source**) and where it should go (**Destination**).

### A. Choose Your Project Layout (Topology)

On the **Add Connection** page, select the option that matches your project:

- **One-to-One (1:1)**: Moving data from one old database directly into one new database.
- **Consolidation (2:1 or Multi-Source)**: Combining data from two or more old databases (e.g., merging an old CRM and a separate billing database) into a single new system.

### B. Name Your Databases

Give each system a friendly nickname you recognize (for example: `Legacy Customers`, `New Cloud Store`).

### C. Connect via the Secure Agent

To keep your data safe and private, Migraflow uses a lightweight connector called the **Agent**.

- Migraflow will generate a single secure command on your screen.
- If you have access to your server or laptop with Docker installed, copy and paste this command into your terminal.
- If not, simply click **"Copy Command"** and send it to your company's IT or DevOps team.
- Once the connector starts, the indicator on your screen will turn **Green (Online)**.

---

## 3. Step 2: Exploring Your Data Catalog

Once your connector is online, Migraflow automatically scans the layout of your databases. This takes only a few seconds.

Navigate to **Data Sources / Profiling** to explore what was found:

- **Table List**: See all the tables discovered (e.g., `customers`, `orders`, `invoices`, `products`).
- **Record Estimates**: See approximate row counts so you know how much data exists.
- **Column Details**: Look inside any table to see column names, data formats (text, dates, numbers), and relationships.

> [!TIP]
> You do not need to understand technical database types. Migraflow automatically flags potential issues like empty columns, duplicate identifiers, or missing dates before any migration begins.

---

## 4. Step 3: Creating Your AI Migration Blueprint

This is where the magic happens! Click the purple **"Generate Plan"** button.

### How the AI Assistant Helps You

Migraflow reads the layout of your old system and your new destination, then intelligently matches corresponding fields:

- It knows that `cust_email` in your old database matches `email_address` in your new database.
- It recognizes that `first_name` and `last_name` can be cleanly formatted.
- It figures out the correct order to move items (for example, moving customer accounts before their order history).

### Exploring the Blueprint View

Once the plan is created, you will see a visual interactive blueprint:

- **Mapping Matrix**: A clear side-by-side list showing:
  - **Left Side**: Where data comes from in your old system.
  - **Middle Arrow**: What transformation is happening (e.g., copy directly, convert date format, or combine values).
  - **Right Side**: The destination column where it will land.

```
Old System Column            Transformation Rule             New System Column
┌──────────────────┐        ┌────────────────────┐        ┌──────────────────┐
│  customer_name   │ ───►   │    Direct Copy     │ ───►   │  full_name       │
│  signup_dt       │ ───►   │ Standardize Date   │ ───►   │  created_at      │
│  acc_status      │ ───►   │  Lowercase Text    │ ───►   │  status          │
└──────────────────┘        └────────────────────┘        └──────────────────┘
```

### Refining the Plan in Plain English

You do not have to write code or formulas to adjust the plan. Simply open the **AI Assistant Bar** and type what you want in regular words:

- _"Exclude any customers whose status is 'cancelled'."_
- _"Change phone numbers to international format."_
- _"Map the legacy user ID into the external_reference column."_

The AI will revise the plan and present the updated blueprint for your confirmation.

### Manual Tweaks & Safety Badges

- **Dropdown Selection**: Prefer to map a field yourself? Click on any destination column dropdown to pick the field manually.
- **Readiness Score**: Look at the top right of your plan. You will see a **Plan Readiness Badge**:
  - 🟢 **Ready for Execution**: All columns are safely matched and verified.
  - 🟡 **Review Recommended**: Some optional fields are unmapped. You can proceed or map them first.

---

## 5. Step 4: Running the Migration & Live Tracking

When you are satisfied with the blueprint, click **"Proceed to Execution"**.

### Safety Choices Before Starting

The app will ask you to confirm your migration mode:

1. **Append Mode (Safest / Default)**: Keeps any existing data already in the destination database and adds the new records to it.
2. **Clean Wipe (Truncate)**: Clears out destination tables before moving new data. A red warning box will ask you to confirm this choice before proceeding.

### The Real-Time Progress Monitor

Once started, you can watch the migration happen live:

- **Overall Progress Bar**: Displays the total percentage of records transferred.
- **Live Counter**: Shows rows successfully transferred in real time (e.g., `254,000 of 500,000 rows`).
- **Table Breakdown**: Shows the progress of each individual table step-by-step.
- **Control Buttons**:
  - **Pause / Cancel**: Need to halt the move? Click **Cancel Migration**. Migraflow stops the transfer safely without corrupting your databases.
  - **Resume Capability**: If your computer loses connection or the internet blinks, Migraflow remembers exactly where it stopped and can resume from the last saved checkpoint.

---

## 6. Step 5: Completion & Verification

When all progress bars reach **100%**, the screen displays a **"Migration Completed"** success badge.

### What to Review:

- **Total Rows Transferred**: Confirms that the expected number of records arrived in your new system.
- **Error Log / Exceptions**: If any individual rows had corrupt or unreadable data (e.g., an invalid email format), they are highlighted in an **Exception Summary** report so you can review them without stalling the rest of your data.

---

## 7. Frequently Asked Questions (FAQ)

### Will using Migraflow disrupt our existing live systems?

**No.** Migraflow connects to your source databases in **Read-Only** mode. It extracts copies of your data without altering, locking, or deleting your original records.

### Can Migraflow staff or cloud servers view our sensitive customer data?

**Never.** Migraflow uses a "Zero Raw Data" security design. Our cloud application only manages the blueprint instructions. The actual records stream directly from your source database to your destination database within your own network.

### What happens if our internet connection drops during a transfer?

You don't have to restart from scratch! Migraflow saves checkpoints every few seconds. Once your connection returns, the system continues moving data from the exact spot it left off.

### What if I make a mistake while customizing the AI blueprint?

Every plan includes **Version History**. You can click **"Versions"** at the top of the plan to preview earlier drafts and click **"Restore"** with a single click.

### Who should I contact if an Agent shows "Offline"?

Make sure the computer or server running the connector is awake and connected to the internet. If you received the command from your IT team, ask them to confirm that the Docker connector container is running.

---

## 8. Summary: Quick 5-Step Checklist

| :---: | :--- | :--- |
| **1** | **Connect** | Set up source & destination; verify **Green "Online"** badge. |
| **2** | **Catalog** | Review discovered tables and approximate record counts. |
| **3** | **Generate Plan** | Click **"Generate Plan"** to let the AI create the visual blueprint. |
| **4** | **Refine & Approve** | Check mappings, type plain-English adjustments, confirm readiness. |
| **5** | **Execute & Monitor** | Click **"Execute"**, watch live progress bars reach **100%**, and view summary. |

---

_Need additional assistance? Click your user profile in the top-right corner to visit Settings or contact your system administrator._
