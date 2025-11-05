# Pull Request

## Description
Brief description of the changes introduced by this pull request.

## Type of Change
Please delete options that are not relevant.

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring
- [ ] Infrastructure/DevOps changes
- [ ] Security enhancement

## Related Issues
Fixes # (issue number)
Closes # (issue number)
Related to # (issue number)

## Changes Made
### Core Changes
- [ ] API endpoints modified/added
- [ ] Database schema changes
- [ ] ML model updates
- [ ] Infrastructure modifications
- [ ] Configuration changes

### Files Modified
List the main files that were changed and why:
- `path/to/file.py`: Brief description of changes
- `path/to/another/file.sql`: Brief description of changes

## Testing
### Test Coverage
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Load tests added/updated (if applicable)
- [ ] Manual testing completed

### Test Results
```bash
# Paste test execution results here
pytest tests/ -v
```

### Performance Impact
- [ ] No performance impact
- [ ] Performance improved
- [ ] Performance degraded (explain below)
- [ ] Performance impact unknown/not measured

Performance details:
```
# Include performance test results if applicable
```

## Code Quality
### Pre-submission Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review of code completed
- [ ] Code is properly commented
- [ ] Documentation updated (if needed)
- [ ] No new linting errors introduced
- [ ] All tests pass locally

### Code Quality Checks
```bash
# Paste code quality check results
black --check .
flake8 .
mypy services/
```

## Security Considerations
- [ ] No security implications
- [ ] Security review completed
- [ ] Secrets/credentials properly handled
- [ ] Input validation implemented
- [ ] Authorization checks in place

Security notes:
```
# Describe any security considerations or changes
```

## Documentation
- [ ] README updated
- [ ] API documentation updated
- [ ] Code comments added/updated
- [ ] Architecture documentation updated
- [ ] Deployment guide updated

## Database Changes
- [ ] No database changes
- [ ] Schema migrations included
- [ ] Data migrations required
- [ ] Backward compatible changes only

Migration details:
```sql
-- Include migration scripts or describe changes
```

## Infrastructure Changes
- [ ] No infrastructure changes
- [ ] Docker configuration updated
- [ ] Kubernetes manifests updated
- [ ] CI/CD pipeline modified
- [ ] Monitoring/alerting updated

Infrastructure notes:
```yaml
# Describe infrastructure changes
```

## Deployment Notes
### Pre-deployment Requirements
- [ ] Database migrations need to be run
- [ ] Configuration changes required
- [ ] Infrastructure updates needed
- [ ] Third-party service updates required

### Deployment Steps
1. Step 1
2. Step 2
3. Step 3

### Rollback Plan
Describe how to rollback these changes if needed:
1. Rollback step 1
2. Rollback step 2

## Breaking Changes
- [ ] No breaking changes
- [ ] Breaking changes included (describe below)

Breaking change details:
```
# Describe breaking changes and migration path
```

## Screenshots/Demos
If applicable, add screenshots or demo videos to showcase the changes.

## Additional Notes
Add any additional context, concerns, or notes for reviewers.

## Reviewer Guidelines
### Focus Areas for Review
- [ ] Code logic and implementation
- [ ] Performance implications
- [ ] Security considerations
- [ ] Test coverage and quality
- [ ] Documentation completeness
- [ ] Breaking change impact

### Specific Review Requests
Please pay special attention to:
- Specific area 1
- Specific area 2

## Post-Merge Tasks
- [ ] Update project documentation
- [ ] Notify stakeholders
- [ ] Monitor deployment
- [ ] Update related issues
- [ ] Create follow-up tasks (if needed)

---

**By submitting this pull request, I confirm that:**
- [ ] I have read and followed the contributing guidelines
- [ ] My code follows the project's coding standards
- [ ] I have tested my changes thoroughly
- [ ] I have updated documentation as needed
- [ ] I understand this will be reviewed before merging
