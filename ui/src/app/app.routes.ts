import { Routes } from '@angular/router';
import { DashboardComponent } from './dashboard/dashboard';
import { ConversationsComponent } from './conversations/conversations';
import { ConversationDetailsComponent } from './conversation-details/conversation-details';
import { AnalyzerComponent } from './analyzer/analyzer';

export const routes: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'conversations', component: ConversationsComponent },
  { path: 'conversation/:id', component: ConversationDetailsComponent },
  { path: 'analyzer', component: AnalyzerComponent },
  { path: '**', redirectTo: 'dashboard' }
];
