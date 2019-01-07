from datetime import timedelta
import logging
import traceback
from airflow.models import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.python_operator import BranchPythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils import timezone


DAG_ARGUMENTS = {
    'schedule_interval': None,
    'dagrun_timeout': None,
    'catchup': False,
    'default_args': {
        'owner': 'airflow',
        'retries': 0,
        'retry_delay': timedelta(minutes=5)}}


class WorkflowFailedException(Exception):
    pass


class iBridgesDag(DAG):
    def __init__(self, dag_id, context, **kwargs):
        self.context = context
        _kwargs = DAG_ARGUMENTS.copy()
        _kwargs.update(kwargs)
        _kwargs['dag_id'] = dag_id
        super(iBridgesDag, self).__init__(**_kwargs)

    def branch_task(self, taskfn, **kwargs):
        def branch_func(**_kwargs):
            logger = logging.getLogger('ipublish')
            taskfn = _kwargs.pop('python_real_callable')
            success = _kwargs.get('task_id') + '_success'
            error = _kwargs.get('task_id') + '_error'
            try:
                taskfn(**_kwargs)
                return success
            except Exception:
                logger.error(traceback.format_exc())
                return error

        _kwargs = {
            'provide_context': True,
            'task_id': taskfn.__name__,
            'op_args': [],
            'op_kwargs': {'ibcontext': self.context,
                          'python_real_callable': taskfn},
            'start_date': timezone.utcnow(),
            'retries': 0
        }
        _kwargs.update(kwargs)
        _kwargs['dag'] = self
        _kwargs['python_callable'] = branch_func
        _kwargs['op_kwargs']['task_id'] = _kwargs.get('task_id')
        success = _kwargs.get('task_id') + '_success'
        error = _kwargs.get('task_id') + '_error'
        op = BranchPythonOperator(**_kwargs)
        succ_op = DummyOperator(task_id=success, dag=self,
                                start_date=_kwargs.get('start_date'))
        error_op = DummyOperator(task_id=error, dag=self,
                                 start_date=_kwargs.get('start_date'))
        op >> succ_op
        op >> error_op
        return op, succ_op, error_op

    def task(self, taskfn, branch=None, **kwargs):
        _kwargs = {
            'provide_context': True,
            'task_id': taskfn.__name__,
            'op_args': [],
            'op_kwargs': {'ibcontext': self.context},
            'start_date': timezone.utcnow(),
            'retries': 0
        }
        _kwargs.update(kwargs)
        _kwargs['dag'] = self
        _kwargs['python_callable'] = taskfn
        _kwargs['op_kwargs']['task_id'] = _kwargs.get('task_id')
        if branch is None:
            op = PythonOperator
        else:
            if 'trigger_rule' not in _kwargs:
                _kwargs['trigger_rule'] = 'all_done'
            _kwargs['op_kwargs']['branch'] = branch
            op = BranchPythonOperator
        return op(**_kwargs)

    def init_task(self):
        def init_fun(**kwargs):
            pass

        return PythonOperator(provide_context=True,
                              task_id='init',
                              op_kwargs={'ibcontext': self.context},
                              start_date=timezone.utcnow(),
                              retries=0,
                              dag=self,
                              python_callable=init_fun)

    def final_task(self, success=True):
        def final_fun(**kwargs):
            if not kwargs.pop('success'):
                raise WorkflowFailedException()

        task_id = 'final_ok' if success else 'final_failed'
        return PythonOperator(provide_context=True,
                              task_id=task_id,
                              op_kwargs={'ibcontext': self.context,
                                         'success': success},
                              start_date=timezone.utcnow(),
                              retries=0,
                              dag=self,
                              python_callable=final_fun)
