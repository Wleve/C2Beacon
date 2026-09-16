import asyncio
import aiosqlite
 
from app.core.models import TaskRecord, TaskResult

class TaskManager:
    def __init__(self):
        self._queues: dict[str, asyncio.Queue[TaskRecord]] = {}
    
    def _ensure_queue(self, beacon_id: str) -> asyncio.Queue[TaskRecord]:
        if beacon_id not in self._queues:
            self._queues=asyncio.Queue
        
        else:
            return self._queues[beacon_id]
        
    
    async def submit(
        self,
        task:TaskRecord,
        db: aiosqlite.Connection,
    ) -> None:
        await db.execute(
            """
            INSERT INTO tasks
                (id,
                beacon_id,
                command,
                args,
                status,
                created_at)
                VALUES (?,?,?,?,?)
            """,
            (task.id,
             task.beacon_id,
             task.command,
             task.args,
             task.status,
             task.created_at),
        )
        await db.commit()
        queue = self._ensure_queue(task.beacon_id)
        await queue._put(task)
        
        
    
    async def get_next(self,beacon_id:str,)->TaskRecord:
        queue = self._ensure_queue(beacon_id) 
        return await queue.get
    
    async def store_result(
        self,
        result:TaskResult,
        db: aiosqlite.Connection,
    )->None:
        await db.execute(
                """
                INSERT INTO task_results
                    (id        
                    task_id    
                    output     
                    error      
                    created_at)
                    VALUES (?,?,?,?,?)
                """,
                (result.id,
                 result.task_id,
                 result.output,
                 result.error,
                 result.created_at,),
            )
        await db.execute(
        """
        UPDATE tasks SET status = 'completed' completed_at = ? WHERE id = ?
        """,
        (result.created_at,result.task_id),
        )
        await db.commit()
                
    
    async def get_history(
        self, beacon_id:str, db:aiosqlite.Connection,
    )-> list[dict[str, str| None]]:
        cursor = await db.execute(
        """
        SELECT t.id, t.args, t.command, t.status, t.created_at, t.completed_at, tr.output, tr.error
        FROM tasks t
        LEFT JOIN task_results tr ON t.id = tr.task id
        WHERE tr.beacon_id = ?
        ORDER BY t.created_at DESC
        """,
        (beacon_id),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    
    def remove_queue(self, beacon_id: str)-> None:
        self._queues.pop(beacon_id, None)