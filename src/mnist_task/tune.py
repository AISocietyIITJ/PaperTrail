import optuna
from hydra import compose, initialize
from omegaconf import OmegaConf

from mnist_task.train import run_training


from hydra.core.global_hydra import GlobalHydra


def objective(trial: optuna.Trial) -> float:
    GlobalHydra.instance().clear()
    with initialize(config_path="../../configs", version_base=None):
        cfg = compose(config_name="config")

    cfg.optimizer.lr = trial.suggest_float("lr", 1e-4, 1e-2, log=True)
    cfg.optimizer.weight_decay = trial.suggest_float(
        "weight_decay", 1e-6, 1e-3, log=True
    )
    cfg.trainer.batch_size = trial.suggest_categorical("batch_size", [32, 64, 128])

    OmegaConf.set_struct(cfg, False)
    best_acc, _ = run_training(cfg, log_to_wandb=False)
    return best_acc


if __name__ == "__main__":
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=20)

    print("Best trial:")
    print(study.best_trial.params)
    print(f"Best accuracy: {study.best_trial.value:.4f}")
