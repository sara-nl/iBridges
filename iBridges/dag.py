from datetime import timedelta
from airflow.models import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.models import BaseOperator
from airflow.models import SkipMixin
from airflow.utils.decorators import apply_defaults
from airflow.utils import dates


DAG_ARGUMENTS = {
    'schedule_interval': None,
    'dagrun_timeout': None,
    'catchup': False,
    'default_args': {
        'owner': 'airflow',
        'start_date': dates.days_ago(2),
        'retries': 0,
        'retry_delay': timedelta(minutes=5)}}


class WorkflowFailedException(Exception):
    pass


class InitTask(BaseOperator):
    ui_color = '#A6E6A6'

    @apply_defaults
    def __init__(self, *args, **kwargs):
        kwargs['op_kwargs'] = kwargs.get('op_kwargs', {})
        _kwargs = {'task_id': 'init',
                   'retries': 0}
        _kwargs.update(kwargs)
        super(InitTask, self).__init__(*args, **_kwargs)

    def execute(self, context):
        pass


class FinalTask(BaseOperator):
    ui_color = '#A6E6A6'

    @apply_defaults
    def __init__(self, *args, **kwargs):
        kwargs['op_kwargs'] = kwargs.get('op_kwargs', {})
        _kwargs = {'task_id': 'init',
                   'retries': 0}
        _kwargs.update(kwargs)
        super(FinalTask, self).__init__(*args, **_kwargs)

    def execute(self, context):
        pass


class ErrorTask(BaseOperator):
    ui_color = '#FA8072'

    @apply_defaults
    def __init__(self, *args, **kwargs):
        kwargs['op_kwargs'] = kwargs.get('op_kwargs', {})
        _kwargs = {'task_id': 'failed',
                   'retries': 0}
        _kwargs.update(kwargs)
        super(ErrorTask, self).__init__(*args, **_kwargs)

    def execute(self, context):
        raise WorkflowFailedException("failed")


class Task(BaseOperator):

    @apply_defaults
    def __init__(self, *args, **kwargs):
        dag = kwargs.get('dag', None)
        if dag is None:
            raise WorkflowFailedException("missing dag")
        self.ibcontext = None if dag is None else dag.context
        self.taskfn = kwargs.pop('fn')
        self.op_kwargs = {}
        _kwargs = {
            'provide_context': True,
            'task_id': "{0}.{1}".format(self.taskfn.__module__,
                                        self.taskfn.__name__),
            'op_args': [],
            'op_kwargs': {},
            'retries': 0
        }
        _kwargs['op_kwargs'].update(kwargs.get('op_kwargs', {}))
        _kwargs.update(kwargs)
        _kwargs['dag'] = self
        _kwargs.update(kwargs)
        self.default_args = {}
        self.op_kwargs = _kwargs.get('op_kwargs', {})
        super(Task, self).__init__(*args, **_kwargs)

    def execute(self, context):
        return self.taskfn(self.ibcontext, **context)


class BranchTask(Task, SkipMixin):
    def execute(self, context):
        branch = super(BranchTask, self).execute(context)
        self.skip_all_except(context['ti'], branch)


class iBridgesDag(DAG):
    def __init__(self, dag_id, context, **kwargs):
        self.context = context
        _kwargs = DAG_ARGUMENTS.copy()
        _kwargs.update(kwargs)
        _kwargs['dag_id'] = dag_id
        super(iBridgesDag, self).__init__(**_kwargs)

    def branch_task(self, taskfn, **kwargs):
        kwargs['fn'] = taskfn
        return BranchTask(dag=self, **kwargs)

    def task(self, taskfn, **kwargs):
        kwargs['fn'] = taskfn
        return Task(dag=self, **kwargs)

    def dummy_operator(self, id, **kwargs):
        return DummyOperator(task_id=id, dag=self, **kwargs)

    def init_task(self, **kwargs):
        return InitTask(dag=self, **kwargs)

    def final_task(self, **kwargs):
        if kwargs.get('task_id', None) is None:
            kwargs['task_id'] = 'final'
        return FinalTask(dag=self, **kwargs)

    def error_task(self, task_id=None):
        if task_id is None:
            task_id = 'final_failed'
        return ErrorTask(dag=self, task_id=task_id)
