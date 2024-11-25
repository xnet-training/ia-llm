# Problem
User asked for current time in timezone
# Solution
Use code_execution_tool with following python code adjusted for your timezone
~~~python
from datetime import datetime
import pytz

timezone = pytz.timezone('America/Lima')
current_time = datetime.now(timezone)

print("Current time in Lima:", current_time)
~~~
