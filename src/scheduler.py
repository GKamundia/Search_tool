import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask

from src.models import SavedSearch, db
from src.alert_service import AlertService
from src.email_service import EmailService

class AlertScheduler:
    """Scheduler for running alerts at configured frequencies"""
    
    def __init__(self, app: Flask):
        self.scheduler = BackgroundScheduler()
        self.app = app
        self.logger = logging.getLogger(__name__)
        self.alert_service = AlertService(app)
        self.email_service = EmailService(app)
    
    def start(self):
        """Start the scheduler with configured jobs"""
        # Add daily job (runs at 1 AM)
        self.scheduler.add_job(
            self._run_frequency_alerts,
            CronTrigger(hour=1, minute=0),
            args=['daily'],
            id='daily_alerts',
            replace_existing=True
        )
        
        # Add weekly job (runs at 2 AM on Mondays)
        self.scheduler.add_job(
            self._run_frequency_alerts,
            CronTrigger(day_of_week=0, hour=2, minute=0),
            args=['weekly'],
            id='weekly_alerts',
            replace_existing=True
        )
        
        # Add monthly job (runs at 3 AM on the 1st of each month)
        self.scheduler.add_job(
            self._run_frequency_alerts,
            CronTrigger(day=1, hour=3, minute=0),
            args=['monthly'],
            id='monthly_alerts',
            replace_existing=True
        )
        
        # Start the scheduler
        self.scheduler.start()
        self.logger.info("Alert scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.logger.info("Alert scheduler stopped")
    
    def _run_frequency_alerts(self, frequency: str):
        """Run alerts for saved searches with the specified frequency"""
        with self.app.app_context():
            self.logger.info(f"Running {frequency} alerts")
            
            # Get all active saved searches with this frequency
            searches = SavedSearch.query.filter_by(
                frequency=frequency,
                active=True
            ).all()
            
            self.logger.info(f"Found {len(searches)} active {frequency} searches")
            
            for search in searches:
                try:
                    # Check for new papers
                    result = self.alert_service.check_for_new_papers(search)
                    new_papers = result.get('new_papers', [])
                    
                    # If new papers found, send notifications
                    if new_papers:
                        self.logger.info(f"Found {len(new_papers)} new papers for search '{search.name}'")
                        
                        # Send email notification if user email is set
                        if search.user_email:
                            self.email_service.send_new_papers_notification(
                                search.user_email, 
                                search, 
                                new_papers
                            )
                    else:
                        self.logger.info(f"No new papers found for search '{search.name}'")
                    
                    # Update the last check timestamp
                    search.last_check_timestamp = datetime.utcnow()
                    db.session.commit()
                    
                except Exception as e:
                    self.logger.error(f"Error running alert for search '{search.name}': {str(e)}")
                    db.session.rollback()
    
    def run_search_now(self, search_id: int) -> dict:
        """
        Manually run a specific saved search
        
        Args:
            search_id: ID of the saved search to run
            
        Returns:
            dict: Result of the alert check
        """
        with self.app.app_context():
            search = SavedSearch.query.get(search_id)
            if not search:
                self.logger.warning(f"Search with ID {search_id} not found")
                return {'error': 'Search not found'}
            
            try:
                # Check for new papers
                result = self.alert_service.check_for_new_papers(search)
                new_papers = result.get('new_papers', [])
                
                # If new papers found, send notifications
                if new_papers and search.user_email:
                    self.email_service.send_new_papers_notification(
                        search.user_email, 
                        search, 
                        new_papers
                    )
                
                # Update the last check timestamp
                search.last_check_timestamp = datetime.utcnow()
                db.session.commit()
                
                return {
                    'success': True,
                    'search_name': search.name,
                    'new_papers_count': len(new_papers)
                }
                
            except Exception as e:
                self.logger.error(f"Error running manual alert for search '{search.name}': {str(e)}")
                db.session.rollback()
                return {'error': str(e)}
