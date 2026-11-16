from django.db import migrations

def forwards(apps,schema_editor):
    vendor=schema_editor.connection.vendor
    if vendor=='postgresql':
        schema_editor.execute('''CREATE FUNCTION core_check_placement_site() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
          IF (SELECT site_id FROM core_miner WHERE id=NEW.miner_id) IS DISTINCT FROM (SELECT r.site_id FROM core_rackslot s JOIN core_rack r ON r.id=s.rack_id WHERE s.id=NEW.slot_id) THEN
            RAISE EXCEPTION 'placement_site_mismatch' USING ERRCODE='23514';
          END IF; RETURN NEW; END $$''')
        schema_editor.execute('CREATE TRIGGER placement_site_guard BEFORE INSERT OR UPDATE ON core_placement FOR EACH ROW EXECUTE FUNCTION core_check_placement_site()')
        schema_editor.execute('''CREATE FUNCTION core_guard_placed_parent() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
          IF TG_TABLE_NAME='core_miner' THEN
            IF NEW.site_id<>OLD.site_id AND EXISTS(SELECT 1 FROM core_placement WHERE miner_id=NEW.id) THEN RAISE EXCEPTION 'placed_miner_site_change' USING ERRCODE='23514'; END IF;
          ELSIF TG_TABLE_NAME='core_rack' THEN
            IF NEW.site_id<>OLD.site_id AND EXISTS(SELECT 1 FROM core_placement p JOIN core_rackslot s ON s.id=p.slot_id WHERE s.rack_id=NEW.id) THEN RAISE EXCEPTION 'placed_rack_site_change' USING ERRCODE='23514'; END IF;
          END IF; RETURN NEW; END $$''')
        for table in ('core_miner','core_rack'):
            schema_editor.execute(f'CREATE TRIGGER {table}_site_guard BEFORE UPDATE OF site_id ON {table} FOR EACH ROW EXECUTE FUNCTION core_guard_placed_parent()')
        schema_editor.execute('''CREATE FUNCTION core_guard_slot_rack() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
          IF EXISTS(SELECT 1 FROM core_placement p JOIN core_miner m ON m.id=p.miner_id JOIN core_rack r ON r.id=NEW.rack_id WHERE p.slot_id=NEW.id AND m.site_id<>r.site_id) THEN RAISE EXCEPTION 'placed_slot_site_change' USING ERRCODE='23514'; END IF; RETURN NEW; END $$''')
        schema_editor.execute('CREATE TRIGGER core_slot_rack_guard BEFORE UPDATE OF rack_id ON core_rackslot FOR EACH ROW EXECUTE FUNCTION core_guard_slot_rack()')
    elif vendor=='sqlite':
        condition='(SELECT site_id FROM core_miner WHERE id=NEW.miner_id) != (SELECT r.site_id FROM core_rackslot s JOIN core_rack r ON r.id=s.rack_id WHERE s.id=NEW.slot_id)'
        for action in ('INSERT','UPDATE'):
            schema_editor.execute(f"CREATE TRIGGER placement_site_guard_{action.lower()} BEFORE {action} ON core_placement WHEN {condition} BEGIN SELECT RAISE(ABORT,'placement_site_mismatch'); END")
        schema_editor.execute("CREATE TRIGGER core_miner_site_guard BEFORE UPDATE OF site_id ON core_miner WHEN NEW.site_id!=OLD.site_id AND EXISTS(SELECT 1 FROM core_placement WHERE miner_id=NEW.id) BEGIN SELECT RAISE(ABORT,'placed_miner_site_change'); END")
        schema_editor.execute("CREATE TRIGGER core_rack_site_guard BEFORE UPDATE OF site_id ON core_rack WHEN NEW.site_id!=OLD.site_id AND EXISTS(SELECT 1 FROM core_placement p JOIN core_rackslot s ON s.id=p.slot_id WHERE s.rack_id=NEW.id) BEGIN SELECT RAISE(ABORT,'placed_rack_site_change'); END")
        schema_editor.execute("CREATE TRIGGER core_slot_rack_guard BEFORE UPDATE OF rack_id ON core_rackslot WHEN EXISTS(SELECT 1 FROM core_placement p JOIN core_miner m ON m.id=p.miner_id JOIN core_rack r ON r.id=NEW.rack_id WHERE p.slot_id=NEW.id AND m.site_id!=r.site_id) BEGIN SELECT RAISE(ABORT,'placed_slot_site_change'); END")

def backwards(apps,schema_editor):
    if schema_editor.connection.vendor=='postgresql':
        schema_editor.execute('DROP TRIGGER IF EXISTS placement_site_guard ON core_placement')
        schema_editor.execute('DROP TRIGGER IF EXISTS core_miner_site_guard ON core_miner')
        schema_editor.execute('DROP TRIGGER IF EXISTS core_rack_site_guard ON core_rack')
        schema_editor.execute('DROP TRIGGER IF EXISTS core_slot_rack_guard ON core_rackslot')
        for name in ('core_check_placement_site','core_guard_placed_parent','core_guard_slot_rack'):schema_editor.execute(f'DROP FUNCTION IF EXISTS {name}()')
    else:
        for name in ('placement_site_guard_insert','placement_site_guard_update','core_miner_site_guard','core_rack_site_guard','core_slot_rack_guard'):schema_editor.execute(f'DROP TRIGGER IF EXISTS {name}')

class Migration(migrations.Migration):
    dependencies=[('core','0001_initial')]
    operations=[migrations.RunPython(forwards,backwards)]
